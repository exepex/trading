"""Story A19 criteria 7 (window), 9 (stale by NSE's calendar) and 10's overnight edge."""

from datetime import time, timedelta

import pytest

from fno.news.reader import CLOSED_DAY, SESSION_HOURS, SESSION_NIGHT, day_type
from fno.news.settings import Window
from fno.news.stale import StaleRule
from fno.news.window import PollingWindow
from fno.research_data.calendar import CsvSessionCalendar
from tests.news.fakes import MARKETS, RBI, calendar, ist

WINDOW = PollingWindow(Window(time(7), time(23)))


@pytest.mark.parametrize(
    "moment, open_",
    [(ist(2026, 10, 16, 7, 0), True), (ist(2026, 10, 16, 6, 59, 59), False), (ist(2026, 10, 16, 22, 59), True),
     (ist(2026, 10, 16, 23, 0), False)],
)  # fmt: skip
def test_window_edges(moment, open_):
    assert WINDOW.is_open(moment) is open_


def test_next_open_and_close():
    night = ist(2026, 10, 16, 23, 30)
    assert WINDOW.next_open(night) == ist(2026, 10, 17, 7, 0)
    assert WINDOW.next_open(ist(2026, 10, 17, 3, 0)) == ist(2026, 10, 17, 7, 0)
    assert WINDOW.next_close(ist(2026, 10, 16, 10, 0)) == ist(2026, 10, 16, 23, 0)


def test_time_open_skips_the_closed_night():
    assert WINDOW.time_open(ist(2026, 10, 16, 22, 55), ist(2026, 10, 17, 7, 0)) == timedelta(minutes=5)
    assert WINDOW.time_open(ist(2026, 10, 16, 10, 0), ist(2026, 10, 16, 10, 16)) == timedelta(minutes=16)


def test_all_day_window():
    always = PollingWindow(Window(time(0), time(0)))
    assert always.is_open(ist(2026, 10, 16, 3, 0)) and always.next_close(ist(2026, 10, 16, 3, 0)) is None


RULE = StaleRule(calendar())


@pytest.mark.parametrize(
    "silence, stale",
    [(timedelta(hours=3), False), (timedelta(hours=2, minutes=59), False), (timedelta(hours=3, minutes=1), True)],
)
def test_session_afternoon_limit_at_under_and_over(silence, stale):
    now = ist(2026, 10, 16, 14, 0)  # a Friday session
    assert RULE.is_stale(MARKETS, now - silence, now) is stale


def test_a_session_night_adds_no_session_hours():
    assert not RULE.is_stale(MARKETS, ist(2026, 10, 15, 18, 0), ist(2026, 10, 16, 9, 0))


def test_monday_0915_after_a_silent_weekend_is_not_stale():
    assert RULE.session_time(ist(2026, 10, 17, 22, 0), ist(2026, 10, 19, 9, 15)) == timedelta(minutes=15)
    assert not RULE.is_stale(RBI, ist(2026, 10, 17, 22, 0), ist(2026, 10, 19, 9, 15))


@pytest.mark.parametrize(
    "silence, stale",
    [(timedelta(hours=20), False), (timedelta(hours=24), False), (timedelta(hours=24, minutes=1), True)],
)
def test_sunday_and_holiday_use_the_all_hours_limit(silence, stale):
    sunday, holiday = ist(2026, 10, 18, 23, 0), ist(2026, 11, 10, 23, 30)
    assert RULE.is_stale(MARKETS, sunday - silence, sunday) is stale
    assert RULE.session_time(ist(2026, 11, 10, 0, 0), holiday) == timedelta(0)  # Diwali: no session hours
    assert RULE.is_stale(MARKETS, holiday - silence, holiday) is stale


def test_a_day_past_the_calendar_counts_as_a_weekday_session():
    rule = StaleRule(CsvSessionCalendar("date,kind,description,source_url\n2026-11-10,holiday,x,https://x\n"))
    assert rule.session_time(ist(2027, 1, 4, 9, 0), ist(2027, 1, 4, 18, 0)) == timedelta(hours=9)


def test_day_types_for_quiet_spells():
    assert day_type(ist(2026, 10, 16, 10, 0), RULE) == SESSION_HOURS
    assert day_type(ist(2026, 10, 16, 20, 0), RULE) == SESSION_NIGHT
    assert day_type(ist(2026, 10, 18, 10, 0), RULE) == CLOSED_DAY
