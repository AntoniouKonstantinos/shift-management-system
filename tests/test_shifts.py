from datetime import date, time, timedelta

import pytest
from sqlalchemy import event

from app import db
from app.models import (
    ACCESS_EMPLOYEE, ACCESS_MANAGER, Department, Employee, Role, Shift, ShiftAssignment,
    UserAccount,
)

PASSWORD = "password123"
FRIDAY = date(2026, 9, 4)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def staff_world(app):
    """A manager, an employee (Elena) and two departments, all with working logins."""
    role = Role(name="Bartender", hourly_rate=7.5)
    bar = Department(name="Bar")
    kitchen = Department(name="Kitchen")
    db.session.add_all([role, bar, kitchen])
    db.session.commit()

    world = {"bar": bar, "kitchen": kitchen}
    for key, name, email, level in [
        ("manager", "Anna Vasileiou", "manager@example.com", ACCESS_MANAGER),
        ("elena", "Elena Ioannou", "elena@example.com", ACCESS_EMPLOYEE),
    ]:
        employee = Employee(
            full_name=name, email=email, role_id=role.id, hire_date=date(2024, 1, 1)
        )
        db.session.add(employee)
        db.session.commit()

        account = UserAccount(employee=employee, access_level=level)
        account.set_password(PASSWORD)
        db.session.add(account)
        db.session.commit()
        world[key] = employee
    return world


def headers_for(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {response.get_json()['access_token']}"}


def make_shift(department, day, start, end, required_staff=1):
    shift = Shift(
        department_id=department.id, shift_date=day,
        start_time=start, end_time=end, required_staff=required_staff,
    )
    db.session.add(shift)
    db.session.commit()
    return shift


def assign(employee, shift, status="assigned"):
    assignment = ShiftAssignment(employee_id=employee.id, shift_id=shift.id, status=status)
    db.session.add(assignment)
    db.session.commit()
    return assignment


def count_queries(action):
    """Run an action and return how many SQL statements it caused."""
    statements = []

    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(db.engine, "before_cursor_execute", record)
    try:
        action()
    finally:
        event.remove(db.engine, "before_cursor_execute", record)
    return len(statements)


# --- departments ---

def test_departments_require_authentication(client, staff_world):
    assert client.get("/api/departments").status_code == 401


def test_an_employee_can_list_departments_sorted_by_name(client, staff_world):
    headers = headers_for(client, "elena@example.com")
    response = client.get("/api/departments", headers=headers)
    assert response.status_code == 200
    assert [d["name"] for d in response.get_json()] == ["Bar", "Kitchen"]


# --- assignments shown on shifts ---

def test_the_shift_list_includes_the_names_of_assigned_staff(client, staff_world):
    shift = make_shift(staff_world["bar"], FRIDAY, time(20, 0), time(2, 0))
    assignment = assign(staff_world["elena"], shift)

    headers = headers_for(client, "elena@example.com")
    [item] = client.get("/api/shifts", headers=headers).get_json()

    assert item["assigned_count"] == 1
    assert item["assignments"] == [{
        "id": assignment.id,
        "employee_id": staff_world["elena"].id,
        "employee": "Elena Ioannou",
        "status": "assigned",
    }]


def test_a_single_shift_includes_its_assignments(client, staff_world):
    shift = make_shift(staff_world["bar"], FRIDAY, time(20, 0), time(2, 0))
    assign(staff_world["elena"], shift)

    headers = headers_for(client, "elena@example.com")
    item = client.get(f"/api/shifts/{shift.id}", headers=headers).get_json()
    assert [a["employee"] for a in item["assignments"]] == ["Elena Ioannou"]


def test_the_shift_list_does_not_run_more_queries_as_shifts_are_added(client, staff_world):
    headers = headers_for(client, "elena@example.com")

    first = make_shift(staff_world["bar"], FRIDAY, time(20, 0), time(2, 0))
    assign(staff_world["elena"], first)
    assign(staff_world["manager"], first)
    with_one_shift = count_queries(lambda: client.get("/api/shifts", headers=headers))

    for offset in range(1, 10):
        shift = make_shift(staff_world["bar"], FRIDAY + timedelta(days=offset), time(20, 0), time(2, 0))
        assign(staff_world["elena"], shift)
        assign(staff_world["manager"], shift)
    with_ten_shifts = count_queries(lambda: client.get("/api/shifts", headers=headers))

    assert with_ten_shifts == with_one_shift


# --- listing rules ---

def test_the_shift_list_is_ordered_by_date_then_start_time(client, staff_world):
    late = make_shift(staff_world["bar"], FRIDAY, time(20, 0), time(2, 0))
    early = make_shift(staff_world["kitchen"], FRIDAY, time(11, 0), time(22, 0))
    next_day = make_shift(staff_world["kitchen"], FRIDAY + timedelta(days=1), time(9, 0), time(15, 0))

    headers = headers_for(client, "elena@example.com")
    ids = [s["id"] for s in client.get("/api/shifts", headers=headers).get_json()]
    assert ids == [early.id, late.id, next_day.id]


def test_the_shift_list_can_be_limited_to_a_date_range(client, staff_world):
    make_shift(staff_world["bar"], FRIDAY - timedelta(days=7), time(20, 0), time(2, 0))
    inside = make_shift(staff_world["bar"], FRIDAY, time(20, 0), time(2, 0))
    make_shift(staff_world["bar"], FRIDAY + timedelta(days=7), time(20, 0), time(2, 0))

    headers = headers_for(client, "elena@example.com")
    response = client.get("/api/shifts?date_from=2026-09-01&date_to=2026-09-07", headers=headers)
    assert [s["id"] for s in response.get_json()] == [inside.id]


# --- who may change shifts ---

def test_an_employee_cannot_create_a_shift(client, staff_world):
    headers = headers_for(client, "elena@example.com")
    response = client.post("/api/shifts", json={
        "department_id": staff_world["bar"].id, "shift_date": "2026-09-04",
        "start_time": "20:00", "end_time": "02:00",
    }, headers=headers)
    assert response.status_code == 403


def test_a_manager_can_create_update_and_delete_a_shift(client, staff_world):
    headers = headers_for(client, "manager@example.com")

    created = client.post("/api/shifts", json={
        "department_id": staff_world["bar"].id, "shift_date": "2026-09-04",
        "start_time": "20:00", "end_time": "02:00", "required_staff": 2,
    }, headers=headers)
    assert created.status_code == 201
    shift = created.get_json()
    assert shift["ends_next_day"] is True
    assert shift["assignments"] == []

    updated = client.put(f"/api/shifts/{shift['id']}", json={
        "required_staff": 3, "notes": "Live music",
    }, headers=headers)
    assert updated.status_code == 200
    assert updated.get_json()["required_staff"] == 3
    assert updated.get_json()["notes"] == "Live music"

    assert client.delete(f"/api/shifts/{shift['id']}", headers=headers).status_code == 204
    assert client.get(f"/api/shifts/{shift['id']}", headers=headers).status_code == 404


def test_deleting_a_shift_also_removes_its_assignments(client, staff_world):
    shift = make_shift(staff_world["bar"], FRIDAY, time(20, 0), time(2, 0))
    assign(staff_world["elena"], shift)

    headers = headers_for(client, "manager@example.com")
    assert client.delete(f"/api/shifts/{shift.id}", headers=headers).status_code == 204
    assert ShiftAssignment.query.count() == 0



# --- extra fields and input rules ---

def test_shifts_report_their_department_id(client, staff_world):
    shift = make_shift(staff_world["kitchen"], FRIDAY, time(11, 0), time(22, 0))
    headers = headers_for(client, "elena@example.com")
    item = client.get(f"/api/shifts/{shift.id}", headers=headers).get_json()
    assert item["department_id"] == staff_world["kitchen"].id


def new_shift_payload(staff_world, **overrides):
    payload = {
        "department_id": staff_world["bar"].id, "shift_date": "2026-09-04",
        "start_time": "20:00", "end_time": "02:00",
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("value", [0, -1, "two", 1.5, True])
def test_required_staff_must_be_a_whole_number_of_at_least_one(client, staff_world, value):
    headers = headers_for(client, "manager@example.com")
    payload = new_shift_payload(staff_world, required_staff=value)
    assert client.post("/api/shifts", json=payload, headers=headers).status_code == 400


def test_an_invalid_required_staff_on_update_is_rejected_and_changes_nothing(client, staff_world):
    shift = make_shift(staff_world["bar"], FRIDAY, time(20, 0), time(2, 0), required_staff=2)
    headers = headers_for(client, "manager@example.com")

    response = client.put(f"/api/shifts/{shift.id}", json={"required_staff": 0}, headers=headers)
    assert response.status_code == 400

    item = client.get(f"/api/shifts/{shift.id}", headers=headers).get_json()
    assert item["required_staff"] == 2


def test_notes_longer_than_255_characters_are_rejected(client, staff_world):
    headers = headers_for(client, "manager@example.com")
    payload = new_shift_payload(staff_world, notes="x" * 256)
    assert client.post("/api/shifts", json=payload, headers=headers).status_code == 400


def test_notes_of_255_characters_are_accepted(client, staff_world):
    headers = headers_for(client, "manager@example.com")
    payload = new_shift_payload(staff_world, notes="x" * 255)
    assert client.post("/api/shifts", json=payload, headers=headers).status_code == 201