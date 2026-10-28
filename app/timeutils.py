from datetime import date, datetime, time, timedelta

# A Monday, used to lay recurring weekly availability slots onto real calendar dates.
REFERENCE_MONDAY = date(2024, 1, 1)


def crosses_midnight(start: time, end: time) -> bool:
    """A range whose end is earlier than its start finishes on the following day."""
    return end < start


def is_valid_range(start: time, end: time) -> bool:
    """Equal start and end is ambiguous (zero length or a full day), so it is not allowed."""
    return start != end


def to_interval(day: date, start: time, end: time) -> tuple[datetime, datetime]:
    """Turn (day, start, end) into absolute datetimes, moving the end to the next day if needed."""
    start_dt = datetime.combine(day, start)
    end_dt = datetime.combine(day, end)
    if crosses_midnight(start, end):
        end_dt += timedelta(days=1)
    return start_dt, end_dt


def overlaps(a: tuple[datetime, datetime], b: tuple[datetime, datetime]) -> bool:
    """Two intervals overlap when each starts before the other ends. Touching ends do not overlap."""
    return a[0] < b[1] and b[0] < a[1]


def covers(outer: tuple[datetime, datetime], inner: tuple[datetime, datetime]) -> bool:
    """True when the inner interval lies entirely within the outer one."""
    return outer[0] <= inner[0] and outer[1] >= inner[1]


def slot_interval(
    day_of_week: int, start: time, end: time, week_offset: int = 0
) -> tuple[datetime, datetime]:
    """Place a weekly slot (0 = Monday) on the reference week, optionally shifted by whole weeks."""
    anchor = REFERENCE_MONDAY + timedelta(days=day_of_week + 7 * week_offset)
    return to_interval(anchor, start, end)


def weekly_slots_overlap(
    day_a: int, start_a: time, end_a: time,
    day_b: int, start_b: time, end_b: time,
) -> bool:
    """Do two recurring weekly slots overlap, including across the Sunday-to-Monday boundary?"""
    a = slot_interval(day_a, start_a, end_a)
    for week_offset in (-1, 0, 1):
        if overlaps(a, slot_interval(day_b, start_b, end_b, week_offset)):
            return True
    return False