"""Story G7b completion, criterion 20: `first_v4_expiry`, V4's expiry rule shared with A4e's `v4` window (G10), on the
committed NSE session calendar (real holidays, the 2024 special Saturday and the 2026 Diwali muhurat)."""

from datetime import date
from pathlib import Path

import pytest

from fno.forecast_v4_rules.v4_expiry import V4_MIN_SESSIONS, first_v4_expiry, scored_sessions_until
from fno.research_data.calendar import CalendarError, load_session_calendar

ROOT = Path(__file__).resolve().parents[2]
CALENDAR = load_session_calendar(ROOT / "research" / "data" / "calendar" / "nse_sessions.csv")
TUE_27_OCT, TUE_3_NOV, TUE_17_NOV = date(2026, 10, 27), date(2026, 11, 3), date(2026, 11, 17)
MON_9_NOV = date(2026, 11, 9)  # the weekly moved a day earlier for the 10 Nov holiday (a listed date is taken as given)
LISTED_2026 = [
    TUE_27_OCT,
    TUE_3_NOV,
    MON_9_NOV,
    TUE_17_NOV,
    date(2026, 11, 23),
    date(2026, 12, 29),
]  # 24 Nov is a holiday: 23 Nov


def test_five_sessions_is_the_rule():
    assert V4_MIN_SESSIONS == 5


def test_good_a_monday_skips_tuesdays_one_session_weekly_for_the_next_one():
    # Mon 26 Oct: 27 Oct holds 1 session; 3 Nov holds 27, 28, 29, 30 Oct, 2 and 3 Nov = 6.
    assert scored_sessions_until(date(2026, 10, 26), TUE_27_OCT, CALENDAR) == 1
    assert first_v4_expiry(date(2026, 10, 26), LISTED_2026, CALENDAR) == TUE_3_NOV


def test_boundary_exactly_five_sessions_is_taken_and_four_is_not():
    # Tue 27 Oct -> 3 Nov: 28, 29, 30 Oct, 2, 3 Nov = 5 (taken). Wed 28 Oct -> 3 Nov: 4 (not), so the next listed.
    assert scored_sessions_until(TUE_27_OCT, TUE_3_NOV, CALENDAR) == 5
    assert first_v4_expiry(TUE_27_OCT, LISTED_2026, CALENDAR) == TUE_3_NOV
    assert scored_sessions_until(date(2026, 10, 28), TUE_3_NOV, CALENDAR) == 4
    assert first_v4_expiry(date(2026, 10, 28), LISTED_2026, CALENDAR) == MON_9_NOV


def test_a_muhurat_session_is_never_counted():
    # Tue 3 Nov -> Mon 9 Nov: 4, 5, 6 and 9 Nov are regular; Sun 8 Nov's muhurat would make it 5.
    assert scored_sessions_until(TUE_3_NOV, MON_9_NOV, CALENDAR) == 4
    assert first_v4_expiry(TUE_3_NOV, LISTED_2026, CALENDAR) == TUE_17_NOV


def test_a_special_weekend_session_is_never_counted():
    # Thu 18 Jan 2024 -> Thu 25 Jan: 19, 23, 24, 25 regular (22 Jan a holiday); Sat 20 Jan's special would make it 5.
    listed = [date(2024, 1, 25), date(2024, 2, 1), date(2024, 2, 29)]
    assert scored_sessions_until(date(2024, 1, 18), date(2024, 1, 25), CALENDAR) == 4
    assert first_v4_expiry(date(2024, 1, 18), listed, CALENDAR) == date(2024, 2, 1)


def test_the_days_own_expiry_and_past_expiries_are_never_chosen():
    # On expiry day 27 Oct itself, 27 Oct is not after the day; 3 Nov (5 sessions) is. Said plainly: they hold 0
    # sessions anyway, so this also passes without the `e > day` filter (kept for clarity, not for the result).
    assert first_v4_expiry(TUE_27_OCT, [date(2026, 10, 20), TUE_27_OCT, TUE_3_NOV], CALENDAR) == TUE_3_NOV


def test_order_and_repeats_of_the_listing_do_not_matter():
    shuffled = [TUE_17_NOV, TUE_3_NOV, TUE_27_OCT, TUE_3_NOV, MON_9_NOV]
    assert first_v4_expiry(date(2026, 10, 26), shuffled, CALENDAR) == TUE_3_NOV


def test_bad_no_listed_expiry_with_five_sessions_gives_none():
    assert first_v4_expiry(date(2026, 10, 26), [TUE_27_OCT], CALENDAR) is None


def test_empty_listing_gives_none():
    assert first_v4_expiry(date(2026, 10, 26), [], CALENDAR) is None


def test_a_day_past_the_calendar_raises_never_guesses():
    beyond = date(CALENDAR.last.year + 1, 1, 30)
    with pytest.raises(CalendarError):
        first_v4_expiry(date(CALENDAR.last.year, 12, 28), [beyond], CALENDAR)


def test_the_window_is_after_the_day_up_to_and_including_the_expiry():
    # Fri 6 Nov -> Tue 10 Nov (a holiday): only Mon 9 Nov is in (6 Nov, 10 Nov]; the day itself never counts.
    assert scored_sessions_until(date(2026, 11, 6), date(2026, 11, 10), CALENDAR) == 1
    # Sun 1 Nov -> Fri 6 Nov: 2, 3, 4, 5 and 6 Nov; the expiry's own session counts.
    assert scored_sessions_until(date(2026, 11, 1), date(2026, 11, 6), CALENDAR) == 5


def test_a_day_the_calendar_does_not_cover_raises_even_with_nothing_listed_after_it():
    with pytest.raises(CalendarError):
        first_v4_expiry(date(CALENDAR.last.year + 1, 6, 1), [], CALENDAR)
    with pytest.raises(CalendarError):
        first_v4_expiry(date(CALENDAR.first.year - 1, 12, 31), [], CALENDAR)


def test_year_end_21_dec_takes_29_dec_and_22_dec_raises_until_2027_is_in_the_calendar():
    # judge 581 m1: 21 Dec -> 29 Dec holds 22, 23, 24, 28, 29 Dec (25 Dec Christmas) = 5; from 22 Dec only 4, so the
    # next listed expiry (Jan 2027) is needed, and the calendar has no 2027 rows yet (the scheduled task adds them).
    listed = [date(2026, 12, 29), date(2027, 1, 5)]
    assert first_v4_expiry(date(2026, 12, 21), listed, CALENDAR) == date(2026, 12, 29)
    if CALENDAR.last.year == 2026:
        with pytest.raises(CalendarError):
            first_v4_expiry(date(2026, 12, 22), listed, CALENDAR)
    else:  # once 2027 is in, 22 Dec takes the January expiry (at least 23, 24, 28, 29, 30, 31 Dec are sessions)
        assert first_v4_expiry(date(2026, 12, 22), listed, CALENDAR) == date(2027, 1, 5)
