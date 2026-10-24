"""Story O2, rows "Routine never starts" and Drive outage (a)'s next session: a session with no run log is O8's
"never ran" that evening, and the next session opens nothing new for every book (E3's `NO_LOG`), alerts it once,
and still runs its exits."""

from datetime import date, datetime, time

from fno.constants import HEALTH_MISSED
from fno.desk.daily_run import NO_LOG
from fno.health.desk_checks import RunLogCheck
from fno.health.model import Deadline
from fno.models import IST

from .harness import fixture_day

EARLIER, SKIPPED, NEXT = date(2026, 10, 13), date(2026, 10, 14), date(2026, 10, 15)


def blocked_next_session(day) -> None:
    """The next session after a session with no log: every book blocked, one alert, its exits still reviewed."""
    fills, full = day.step("fills")["book1_rules"], day.full_step("fills")["book1_rules"]
    assert fills == {"outcome": "not filled", "reason": "fills:BLOCKED"}  # the public log: status and code only
    assert NO_LOG.format(day=SKIPPED) in full["reason"]  # the full text: the private log and the alert
    assert len([text for text in day.slack.sent if NO_LOG.format(day=SKIPPED) in text]) == 1
    assert day.step("exits")["book1_rules"]["reviewed"] is True


def test_a_routine_that_never_starts_is_o8_s_never_ran_and_the_next_session_opens_nothing_new(tmp_path, monkeypatch):
    day = fixture_day(tmp_path, monkeypatch)
    day.move_to(EARLIER)
    assert day.run() == (0, "day done")  # a normal session before
    day.move_to(NEXT)  # the routine of 14 Oct never started: no run, no log
    evening = datetime.combine(SKIPPED, time(17, 51), IST)
    assert RunLogCheck(day.root, Deadline(time(15, 12))).check(SKIPPED, evening).status == HEALTH_MISSED
    day.run()
    blocked_next_session(day)


def test_after_a_drive_outage_at_the_download_the_next_session_opens_nothing_new(tmp_path, monkeypatch):
    day = fixture_day(tmp_path, monkeypatch)
    day.move_to(EARLIER)
    assert day.run() == (0, "day done")
    day.move_to(SKIPPED)
    day.drive.down = True
    assert "run STOPPED at the download" in day.run()[1]
    day.drive.down = False
    day.slack.sent.clear()
    day.move_to(NEXT)
    day.run()
    blocked_next_session(day)
