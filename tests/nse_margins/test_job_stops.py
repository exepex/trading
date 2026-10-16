"""Response 239 item 4: the margins job names every stop in its one #fno-desk line, so the workflow's "already
alerted" holds: a year missing from A7's calendar (from 1 Jan 2027 until NSE's 2027 rows are added) and a failed
write are alerted by type and message, never only a traceback and a red run."""

from datetime import UTC, date, datetime, time

import yaml

from fno.config import ROOT
from fno.models import IST
from fno.nse_margins.job import due_session
from fno.research_data.calendar import CalendarError

from .span_builder import DAY, span_zip
from .test_job import Alerts, done_before, make_job, margins_file, weekday


def test_a_year_missing_from_the_calendar_is_named_in_the_one_line(tmp_path):
    alerts = Alerts()
    job = make_job(margins_file(tmp_path), {DAY: span_zip()}, alerts=alerts)

    def no_rows(day):
        raise CalendarError(f"{day} is outside the calendar: add every row of NSE's {day.year} holiday circular")

    job.is_trading_day = no_rows
    assert job.run() == 1 and len(alerts.sent) == 1
    assert "stopped by an unexpected CalendarError" in alerts.sent[0] and "holiday circular" in alerts.sent[0]


def test_a_failed_write_is_named_with_its_day(tmp_path):
    alerts = Alerts()
    job = make_job(margins_file(tmp_path, done_before(DAY)), {DAY: span_zip()}, alerts=alerts)

    def disk_full(rows):
        raise OSError("No space left on device")

    job.log.append = disk_full
    assert job.run() == 1 and len(alerts.sent) == 1
    assert f"{DAY}: stopped by an unexpected OSError: No space left on device" in alerts.sent[0]


def test_every_scheduled_slot_runs_on_the_session_s_own_ist_date_before_the_open():
    """All of nse-margins.yml's crons (the main run, two catch-ups after a dropped slot, the retry): on time, each is on
    the session's IST date before 09:15, so any one of them that GitHub starts writes the right day's rows."""
    workflow = yaml.safe_load((ROOT / ".github/workflows/nse-margins.yml").read_text(encoding="utf-8"))
    slots = [entry["cron"].split()[:2] for entry in workflow[True]["schedule"]]
    assert len(slots) == 4
    for minute, hour in slots:
        utc_day = date(2026, 10, 15) if int(hour) >= 18 else date(2026, 10, 16)  # 18:30 UTC is IST midnight
        now = datetime(utc_day.year, utc_day.month, utc_day.day, int(hour), int(minute), tzinfo=UTC).astimezone(IST)
        assert now.date() == date(2026, 10, 16) and now.time() < time(9, 15)
        assert due_session(now, weekday) == date(2026, 10, 16)
