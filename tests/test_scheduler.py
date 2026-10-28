from datetime import date, time
from types import SimpleNamespace

import pytest

from app import db
from app.models import (
    Availability, Department, Employee, Role, Shift, ShiftAssignment, TimeOffRequest,
)
from app.scheduler import (
    _has_conflict, _is_available, _is_on_time_off, get_available_employees,
)

FRIDAY = date(2026, 9, 4)
SATURDAY = date(2026, 9, 5)
FRIDAY_INDEX = 4
SATURDAY_INDEX = 5


@pytest.fixture
def world(app):
    """One bartender, Elena, and one department."""
    role = Role(name="Bartender", hourly_rate=7.5)
    department = Department(name="Bar")
    db.session.add_all([role, department])
    db.session.commit()

    elena = Employee(
        full_name="Elena Ioannou", email="elena@example.com",
        role_id=role.id, hire_date=date(2024, 1, 10),
    )
    db.session.add(elena)
    db.session.commit()
    return SimpleNamespace(elena=elena, department=department)


def add_availability(employee, day_index, start, end):
    db.session.add(Availability(
        employee_id=employee.id, day_of_week=day_index, start_time=start, end_time=end,
    ))
    db.session.commit()


def add_shift(department, day, start, end):
    shift = Shift(
        department_id=department.id, shift_date=day,
        start_time=start, end_time=end, required_staff=1,
    )
    db.session.add(shift)
    db.session.commit()
    return shift


def assign(employee, shift, status="assigned"):
    db.session.add(ShiftAssignment(employee_id=employee.id, shift_id=shift.id, status=status))
    db.session.commit()


# --- availability ---

def test_same_day_availability_covers_a_shift_inside_it(world):
    add_availability(world.elena, 0, time(17, 0), time(23, 0))
    assert _is_available(world.elena, 0, time(18, 0), time(22, 0))


def test_same_day_availability_does_not_cover_a_shift_starting_earlier(world):
    add_availability(world.elena, 0, time(17, 0), time(23, 0))
    assert not _is_available(world.elena, 0, time(16, 0), time(22, 0))


def test_overnight_availability_covers_an_overnight_shift_that_ends_in_time(world):
    add_availability(world.elena, FRIDAY_INDEX, time(18, 0), time(2, 0))
    assert _is_available(world.elena, FRIDAY_INDEX, time(22, 0), time(1, 30))


def test_overnight_availability_does_not_cover_a_shift_that_ends_too_late(world):
    add_availability(world.elena, FRIDAY_INDEX, time(18, 0), time(2, 0))
    assert not _is_available(world.elena, FRIDAY_INDEX, time(22, 0), time(3, 0))


def test_friday_overnight_availability_covers_an_early_saturday_shift(world):
    add_availability(world.elena, FRIDAY_INDEX, time(18, 0), time(2, 0))
    assert _is_available(world.elena, SATURDAY_INDEX, time(0, 30), time(2, 0))


def test_friday_overnight_availability_does_not_cover_a_saturday_shift_running_past_it(world):
    add_availability(world.elena, FRIDAY_INDEX, time(18, 0), time(2, 0))
    assert not _is_available(world.elena, SATURDAY_INDEX, time(0, 30), time(2, 30))


def test_sunday_overnight_availability_covers_an_early_monday_shift(world):
    add_availability(world.elena, 6, time(22, 0), time(2, 0))
    assert _is_available(world.elena, 0, time(0, 0), time(1, 0))


# --- conflicts ---

def test_overnight_assignment_conflicts_with_an_early_shift_the_next_day(world):
    friday_night = add_shift(world.department, FRIDAY, time(22, 0), time(3, 0))
    assign(world.elena, friday_night)
    saturday_early = add_shift(world.department, SATURDAY, time(1, 0), time(5, 0))
    assert _has_conflict(world.elena, saturday_early)


def test_early_assignment_conflicts_with_an_overnight_shift_the_day_before(world):
    saturday_early = add_shift(world.department, SATURDAY, time(1, 0), time(5, 0))
    assign(world.elena, saturday_early)
    friday_night = add_shift(world.department, FRIDAY, time(22, 0), time(3, 0))
    assert _has_conflict(world.elena, friday_night)


def test_shifts_that_only_touch_do_not_conflict(world):
    friday_night = add_shift(world.department, FRIDAY, time(20, 0), time(2, 0))
    assign(world.elena, friday_night)
    saturday_early = add_shift(world.department, SATURDAY, time(2, 0), time(6, 0))
    assert not _has_conflict(world.elena, saturday_early)


def test_no_show_assignments_do_not_cause_conflicts(world):
    first = add_shift(world.department, FRIDAY, time(18, 0), time(23, 0))
    assign(world.elena, first, status="no_show")
    second = add_shift(world.department, FRIDAY, time(20, 0), time(22, 0))
    assert not _has_conflict(world.elena, second)


def test_a_shift_does_not_conflict_with_its_own_assignment(world):
    shift = add_shift(world.department, FRIDAY, time(18, 0), time(23, 0))
    assign(world.elena, shift)
    assert not _has_conflict(world.elena, shift)


# --- time off ---

def test_approved_time_off_blocks_the_shift_start_date(world):
    db.session.add(TimeOffRequest(
        employee_id=world.elena.id, start_date=FRIDAY, end_date=SATURDAY, status="approved",
    ))
    db.session.commit()
    assert _is_on_time_off(world.elena, FRIDAY)


def test_pending_time_off_does_not_block(world):
    db.session.add(TimeOffRequest(
        employee_id=world.elena.id, start_date=FRIDAY, end_date=SATURDAY, status="pending",
    ))
    db.session.commit()
    assert not _is_on_time_off(world.elena, FRIDAY)


# --- the full candidate list ---

def test_candidates_include_elena_for_an_overnight_shift_she_can_cover(world):
    add_availability(world.elena, FRIDAY_INDEX, time(18, 0), time(2, 0))
    shift = add_shift(world.department, FRIDAY, time(22, 0), time(1, 30))
    assert [e.id for e in get_available_employees(shift.id)] == [world.elena.id]


def test_candidates_exclude_elena_for_an_overnight_shift_that_runs_too_late(world):
    add_availability(world.elena, FRIDAY_INDEX, time(18, 0), time(2, 0))
    shift = add_shift(world.department, FRIDAY, time(22, 0), time(3, 0))
    assert get_available_employees(shift.id) == []


def test_candidates_for_an_unknown_shift_are_empty(world):
    assert get_available_employees(9999) == []