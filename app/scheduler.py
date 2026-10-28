from datetime import timedelta

from app import db
from app.models import Employee, Availability, ShiftAssignment, TimeOffRequest, Shift
from app.timeutils import covers, overlaps, slot_interval, to_interval


def get_available_employees(shift_id):
    """
    Returns the active employees who are eligible for a given shift,
    filtered by availability, conflicting assignments and approved time off.
    """
    shift = db.session.get(Shift, shift_id)
    if not shift:
        return []

    day_of_week = shift.shift_date.weekday()  # 0 = Monday ... 6 = Sunday
    candidates = Employee.query.filter_by(is_active=True).all()

    available = []
    for employee in candidates:
        if not _is_available(employee, day_of_week, shift.start_time, shift.end_time):
            continue
        if _has_conflict(employee, shift):
            continue
        if _is_on_time_off(employee, shift.shift_date):
            continue
        available.append(employee)

    return available


def _shift_interval(shift):
    """The shift as absolute datetimes; an end time earlier than the start means the next day."""
    return to_interval(shift.shift_date, shift.start_time, shift.end_time)


def _is_available(employee, day_of_week, start_time, end_time):
    """True when one of the employee's weekly slots fully covers the shift, including overnight slots."""
    shift = slot_interval(day_of_week, start_time, end_time)
    slots = Availability.query.filter_by(employee_id=employee.id).all()

    for slot in slots:
        for week_offset in (-1, 0, 1):
            window = slot_interval(slot.day_of_week, slot.start_time, slot.end_time, week_offset)
            if covers(window, shift):
                return True
    return False


def _has_conflict(employee, shift):
    """True when the employee already has an assignment that overlaps this shift in time."""
    this_interval = _shift_interval(shift)

    nearby = (
        ShiftAssignment.query
        .join(Shift)
        .filter(
            ShiftAssignment.employee_id == employee.id,
            Shift.shift_date >= shift.shift_date - timedelta(days=1),
            Shift.shift_date <= shift.shift_date + timedelta(days=1),
            ShiftAssignment.status != "no_show",
        )
        .all()
    )

    for assignment in nearby:
        other = assignment.shift
        if other.id == shift.id:
            continue
        if overlaps(this_interval, _shift_interval(other)):
            return True
    return False


def _is_on_time_off(employee, shift_date):
    """True when the shift's start date falls inside an approved time-off period."""
    requests = TimeOffRequest.query.filter_by(
        employee_id=employee.id, status="approved"
    ).all()

    for req in requests:
        if req.start_date <= shift_date <= req.end_date:
            return True
    return False