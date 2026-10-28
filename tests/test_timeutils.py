from datetime import date, datetime, time

from app.timeutils import (
    covers,
    crosses_midnight,
    is_valid_range,
    overlaps,
    to_interval,
    weekly_slots_overlap,
)


def dt(day, hour, minute=0):
    """A datetime in September 2026 (the 4th is a Friday)."""
    return datetime(2026, 9, day, hour, minute)


# --- crosses_midnight / is_valid_range ---

def test_same_day_range_does_not_cross_midnight():
    assert not crosses_midnight(time(17, 0), time(23, 0))


def test_overnight_range_crosses_midnight():
    assert crosses_midnight(time(22, 0), time(2, 0))


def test_equal_start_and_end_is_invalid():
    assert not is_valid_range(time(9, 0), time(9, 0))


def test_overnight_and_same_day_ranges_are_valid():
    assert is_valid_range(time(22, 0), time(2, 0))
    assert is_valid_range(time(9, 0), time(17, 0))


# --- to_interval ---

def test_same_day_interval_stays_on_one_date():
    start, end = to_interval(date(2026, 9, 4), time(17, 0), time(23, 0))
    assert start == dt(4, 17)
    assert end == dt(4, 23)


def test_overnight_interval_ends_on_the_next_date():
    start, end = to_interval(date(2026, 9, 4), time(22, 0), time(2, 0))
    assert start == dt(4, 22)
    assert end == dt(5, 2)


# --- overlaps ---

def test_partially_overlapping_intervals_overlap():
    assert overlaps((dt(4, 10), dt(4, 14)), (dt(4, 12), dt(4, 16)))


def test_touching_intervals_do_not_overlap():
    assert not overlaps((dt(4, 10), dt(4, 12)), (dt(4, 12), dt(4, 16)))


def test_separate_intervals_do_not_overlap():
    assert not overlaps((dt(4, 10), dt(4, 12)), (dt(4, 15), dt(4, 18)))


def test_overnight_shift_overlaps_early_shift_on_the_next_day():
    friday_night = to_interval(date(2026, 9, 4), time(22, 0), time(3, 0))
    saturday_early = to_interval(date(2026, 9, 5), time(1, 0), time(5, 0))
    assert overlaps(friday_night, saturday_early)


# --- covers ---

def test_overnight_availability_covers_a_shift_that_ends_in_time():
    availability = to_interval(date(2026, 9, 4), time(18, 0), time(2, 0))
    shift = to_interval(date(2026, 9, 4), time(22, 0), time(1, 30))
    assert covers(availability, shift)


def test_overnight_availability_does_not_cover_a_shift_that_ends_too_late():
    availability = to_interval(date(2026, 9, 4), time(18, 0), time(2, 0))
    shift = to_interval(date(2026, 9, 4), time(22, 0), time(3, 0))
    assert not covers(availability, shift)


# --- weekly_slots_overlap ---

def test_friday_overnight_slot_overlaps_early_saturday_slot():
    assert weekly_slots_overlap(4, time(18, 0), time(2, 0), 5, time(1, 0), time(5, 0))


def test_slots_that_only_touch_across_midnight_do_not_overlap():
    assert not weekly_slots_overlap(4, time(18, 0), time(2, 0), 5, time(2, 0), time(5, 0))


def test_sunday_overnight_slot_overlaps_early_monday_slot():
    assert weekly_slots_overlap(6, time(22, 0), time(2, 0), 0, time(1, 0), time(5, 0))


def test_slots_on_different_days_do_not_overlap():
    assert not weekly_slots_overlap(0, time(10, 0), time(12, 0), 1, time(10, 0), time(12, 0))