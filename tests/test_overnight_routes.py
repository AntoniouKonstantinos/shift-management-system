from datetime import date

import pytest

from app import db
from app.models import (
    ACCESS_EMPLOYEE, ACCESS_MANAGER, Department, Employee, Role, UserAccount,
)

PASSWORD = "password123"


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def people(app):
    """A manager and an employee (Elena), both with accounts, plus one department."""
    role = Role(name="Bartender", hourly_rate=7.5)
    department = Department(name="Bar")
    db.session.add_all([role, department])
    db.session.commit()

    created = {"department": department}
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
        created[key] = employee
    return created


def headers_for(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {response.get_json()['access_token']}"}


def post_slot(client, headers, employee_id, day, start, end):
    return client.post(
        f"/api/employees/{employee_id}/availability",
        json={"day_of_week": day, "start_time": start, "end_time": end},
        headers=headers,
    )


def post_shift(client, headers, department_id, start, end):
    return client.post(
        "/api/shifts",
        json={
            "department_id": department_id,
            "shift_date": "2026-09-04",  # a Friday
            "start_time": start,
            "end_time": end,
        },
        headers=headers,
    )


# --- availability ---

def test_overnight_availability_slot_is_accepted(client, people):
    headers = headers_for(client, "elena@example.com")
    response = post_slot(client, headers, people["elena"].id, 4, "18:00", "02:00")
    assert response.status_code == 201
    assert response.get_json()["ends_next_day"] is True


def test_same_day_slot_is_not_marked_as_ending_next_day(client, people):
    headers = headers_for(client, "elena@example.com")
    response = post_slot(client, headers, people["elena"].id, 4, "17:00", "23:00")
    assert response.status_code == 201
    assert response.get_json()["ends_next_day"] is False


def test_slot_with_equal_start_and_end_is_rejected(client, people):
    headers = headers_for(client, "elena@example.com")
    response = post_slot(client, headers, people["elena"].id, 4, "18:00", "18:00")
    assert response.status_code == 400


def test_slot_overlapping_an_overnight_slot_from_the_previous_day_is_rejected(client, people):
    headers = headers_for(client, "elena@example.com")
    elena_id = people["elena"].id
    assert post_slot(client, headers, elena_id, 4, "18:00", "02:00").status_code == 201
    assert post_slot(client, headers, elena_id, 5, "01:00", "05:00").status_code == 409


def test_slot_that_only_touches_an_overnight_slot_is_accepted(client, people):
    headers = headers_for(client, "elena@example.com")
    elena_id = people["elena"].id
    assert post_slot(client, headers, elena_id, 4, "18:00", "02:00").status_code == 201
    assert post_slot(client, headers, elena_id, 5, "02:00", "05:00").status_code == 201


def test_sunday_overnight_slot_conflicts_with_an_early_monday_slot(client, people):
    headers = headers_for(client, "elena@example.com")
    elena_id = people["elena"].id
    assert post_slot(client, headers, elena_id, 6, "22:00", "02:00").status_code == 201
    assert post_slot(client, headers, elena_id, 0, "01:00", "05:00").status_code == 409


def test_updating_a_slot_does_not_clash_with_itself(client, people):
    headers = headers_for(client, "elena@example.com")
    elena_id = people["elena"].id
    created = post_slot(client, headers, elena_id, 4, "18:00", "02:00").get_json()

    response = client.put(
        f"/api/employees/{elena_id}/availability/{created['id']}",
        json={"end_time": "03:00"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.get_json()["end_time"] == "03:00"


# --- shifts ---

def test_manager_can_create_an_overnight_shift(client, people):
    headers = headers_for(client, "manager@example.com")
    response = post_shift(client, headers, people["department"].id, "22:00", "02:00")
    assert response.status_code == 201
    assert response.get_json()["ends_next_day"] is True


def test_shift_with_equal_start_and_end_is_rejected(client, people):
    headers = headers_for(client, "manager@example.com")
    response = post_shift(client, headers, people["department"].id, "22:00", "22:00")
    assert response.status_code == 400


# --- end to end ---

def test_candidates_endpoint_finds_elena_for_an_overnight_shift_she_can_cover(client, people):
    elena_headers = headers_for(client, "elena@example.com")
    assert post_slot(client, elena_headers, people["elena"].id, 4, "18:00", "02:00").status_code == 201

    manager_headers = headers_for(client, "manager@example.com")
    shift = post_shift(client, manager_headers, people["department"].id, "22:00", "01:30").get_json()

    response = client.get(f"/api/shifts/{shift['id']}/candidates", headers=manager_headers)
    assert response.status_code == 200
    assert [c["id"] for c in response.get_json()] == [people["elena"].id]