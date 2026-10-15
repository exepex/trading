"""Story O8 criterion 1: the window is defined once, so the same session is checked whenever the cron starts, and every
push it can need stays inside GitHub's 7-day activity log, holiday weeks included."""

from datetime import date, datetime, time, timedelta

import pytest

from fno.config import load_app_config
from fno.health.window import window_days, window_sessions
from fno.models import IST
from fno.quotes.recorder import WINDOW_START
from fno.storage.wiring import build_session_calendar

from .fakes import CALENDAR, DAY, ist

DAYS = load_app_config()["health"]["window_days"]
LOG_SPAN = timedelta(days=7)  # GitHub's activity log, `time_period=week` (fno/ai/receipts.py)


def test_the_window_is_six_days():
    assert DAYS == 6


@pytest.mark.parametrize("run", [ist(DAY, 17, 51), ist(DAY, 23, 40), ist(DAY + timedelta(1), 3, 10),
                                 ist(DAY + timedelta(6), 23, 59)])  # fmt: skip
def test_a_session_is_checked_by_every_run_from_its_evening_to_six_days_later(run):
    assert DAY in window_sessions(CALENDAR, run.date(), DAYS)


def test_a_session_leaves_the_window_on_the_seventh_day():
    assert DAY not in window_sessions(CALENDAR, DAY + timedelta(7), DAYS)


def test_closed_days_never_enter_the_window_and_muhurat_does():
    sessions = window_sessions(CALENDAR, date(2026, 10, 22), DAYS)
    assert date(2026, 10, 20) not in sessions and date(2026, 10, 18) not in sessions
    assert date(2026, 10, 21) in sessions


def test_no_window_needs_a_push_older_than_githubs_log_over_every_run_of_2025():
    """The oldest push a run needs is the first session's, made at the earliest 14:55; read at 23:59 on the run day."""
    calendar, worst = build_session_calendar(), timedelta(0)
    for offset in range(365):
        run_day = date(2025, 1, 1) + timedelta(offset)
        sessions = window_sessions(calendar, run_day, DAYS)
        if sessions:
            oldest = datetime.combine(sessions[0], WINDOW_START, IST)
            worst = max(worst, datetime.combine(run_day, time(23, 59), IST) - oldest)
    assert timedelta(days=6) < worst < LOG_SPAN


def test_the_watchers_days_are_the_calendar_days_before_the_run():
    assert window_days(DAY, 3) == [date(2026, 10, 12), date(2026, 10, 13), date(2026, 10, 14)]
