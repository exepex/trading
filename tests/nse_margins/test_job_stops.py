"""Response 239 item 4: the margins job names every stop in its one #fno-desk line, so the workflow's "already
alerted" holds: a year missing from A7's calendar (from 1 Jan 2027 until NSE's 2027 rows are added) and a failed
write are alerted by type and message, never only a traceback and a red run."""

from fno.research_data.calendar import CalendarError

from .span_builder import DAY, span_zip
from .test_job import Alerts, done_before, make_job, margins_file


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
