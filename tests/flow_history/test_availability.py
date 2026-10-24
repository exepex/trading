"""Criterion 2: a file is public from the first session whose 09:15 open is at or after its write time."""

from __future__ import annotations

from datetime import date, datetime, time

import pytest

from fno.flow_history.availability import Availability, availability
from fno.models import IST
from fno.research_data.calendar import CsvSessionCalendar
from fno.storage.trading_days import next_trading_day

SOURCE = "https://nsearchives.nseindia.com/content/circulars/test.pdf"
CALENDAR = CsvSessionCalendar(  # Wed 21 Oct 2026 a holiday, Fri 23 Oct a muhurat-only evening
    f"date,kind,description,source_url\n2026-10-21,holiday,test,{SOURCE}\n2026-10-23,muhurat,test,{SOURCE}\n"
)


def _next(day: date) -> date:
    return next_trading_day(CALENDAR, day)


def ist(day: int, hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime.combine(date(2026, 10, day), time(hour, minute, second), IST)


@pytest.mark.parametrize(
    ("day", "written", "expected"),
    [
        (16, ist(16, 19, 14), Availability(date(2026, 10, 19), False)),  # a Friday's file on Monday
        (20, ist(20, 19, 14), Availability(date(2026, 10, 22), False)),  # before a holiday: the session after it
        (22, ist(22, 19, 14), Availability(date(2026, 10, 26), False)),  # a muhurat-only evening is stepped over
        (19, ist(20, 9, 15), Availability(date(2026, 10, 20), False)),  # written at the next open exactly
        (19, ist(20, 9, 15, 1), Availability(date(2026, 10, 22), True)),  # one second later: rewritten
        (19, ist(26, 8, 0), Availability(date(2026, 10, 26), True)),  # rewritten days later, before an open
        (19, None, Availability(date(2026, 10, 20), True)),  # no write time: unknown, so rewritten
    ],
)
def test_available_from_the_first_session_open_at_or_after_the_write(day, written, expected):
    assert availability(date(2026, 10, day), written, _next) == expected


def test_never_the_same_day():
    assert availability(date(2026, 10, 19), ist(19, 8, 0), _next).available_from == date(2026, 10, 20)
