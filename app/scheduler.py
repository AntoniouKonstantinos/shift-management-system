from datetime import datetime, timedelta
from app.models import Employee, Availability, ShiftAssignment, TimeOffRequest, Shift


def get_available_employees(shift_id):
    """
    Return a list of employees eligible for specific shift,
    based on availability, conflicts and time-off.
    """
    shift = Shift.query.get(shift_id)
    if not shift:
        return []

    day_of_week = shift.shift_date.weekday()  # 0=Monday ... 6=Sunday

    candidates = Employee.query.filter_by(
        role_id=shift.department.name and None or None  # placeholder
    ).all() if False else Employee.query.filter_by(is_active=True).all()

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


def _is_available(employee, day_of_week, start_time, end_time):
    """Check if the employee declared any time off in the shift's timeline."""
    slots = Availability.query.filter_by(
        employee_id=employee.id, day_of_week=day_of_week
    ).all()

    for slot in slots:
        if slot.start_time <= start_time and slot.end_time >= end_time:
            return True
    return False


def _has_conflict(employee, shift):
    """Check if the employee is already assigned to another shift that overlaps in time"""
    existing = (
        ShiftAssignment.query
        .join(Shift)
        .filter(
            ShiftAssignment.employee_id == employee.id,
            Shift.shift_date == shift.shift_date,
            ShiftAssignment.status != "no_show",
        )
        .all()
    )

    for assignment in existing:
        other = assignment.shift
        if other.id == shift.id:
            continue
        if _times_overlap(shift.start_time, shift.end_time, other.start_time, other.end_time):
            return True
    return False


def _times_overlap(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1


def _is_on_time_off(employee, shift_date):
    """Check if the shift date overlaps with a specific time off."""
    requests = TimeOffRequest.query.filter_by(
        employee_id=employee.id, status="approved"
    ).all()

    for req in requests:
        if req.start_date <= shift_date <= req.end_date:
            return True
    return False