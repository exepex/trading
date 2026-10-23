"""Story A14: the daily job appends each session's rows once, point in time, and fails closed with one alert."""

from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import pytest
import yaml

from fno.config import ROOT
from fno.models import IST
from fno.nse_margins.broker_approvals import Approval, BrokerApprovals
from fno.nse_margins.calculator import MarginFigure, NseIndexOptionExposure, SpanMarginCalculator
from fno.nse_margins.job import NseMarginJob, due_session
from fno.nse_margins.margin_log import MarginLog, MarginLogConflict
from fno.nse_margins.rows import MarginRow, MarginRowBuilder
from fno.research_engine.structures import LongIronFly, ShortCondor, ShortIronFly
from fno.risk.inputs import RiskInputError, TradeTerms
from fno.risk.margin_age import DaysOld
from fno.risk.margins import MARGIN_COLUMNS, MarginParts, MarginTable
from fno.storage.row_log import CsvRowLog
from fno.storage.table_source import FileTable

from .span_builder import DAY, LOT, span_zip

HEADER = ",".join(MARGIN_COLUMNS) + "\n"
MORNING = datetime(2026, 10, 14, 7, 45, tzinfo=IST)


def weekday(day: date) -> bool:
    return day.weekday() < 5


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text: str) -> str:
        self.sent.append(text)
        return "alert sent"


def margin_log(path: Path) -> MarginLog:
    """A14's log on a local file (O9b step 2: the wiring's is a receipt-backed Drive series)."""
    return MarginLog(FileTable(path), CsvRowLog(path))


def margins_file(tmp_path: Path, text: str = HEADER) -> Path:
    path = tmp_path / "margins.csv"
    path.write_text(text, encoding="utf-8")
    return path


PASSED = BrokerApprovals({code: Approval("test: broker check", date(2026, 10, 1)) for code in ("SF", "SC", "BF")})


def make_job(path: Path, files: dict[date, bytes], now: datetime = MORNING, alerts: Alerts | None = None,
             check: BrokerApprovals = PASSED, printed: list | None = None):  # fmt: skip
    builder = MarginRowBuilder((ShortIronFly(), ShortCondor(), LongIronFly()), (100.0, 200.0),
                               SpanMarginCalculator(NseIndexOptionExposure(), LOT), 30)  # fmt: skip
    day_file = lambda day: (f"nsccl.{day:%Y%m%d}.i1.zip", files.get(day))  # noqa: E731
    out = printed.append if printed is not None else (lambda _: None)
    return NseMarginJob(day_file, builder, margin_log(path), weekday, check, alerts or Alerts(), lambda: now, out)


def done_before(day: date) -> str:
    """Rows for the week before `day`, so only `day` is pending."""
    rows = [f"SF,100,1.00,0,0,NSE SPAN old sha256=00,{day - timedelta(days=n)}\n" for n in range(1, 8)]
    return HEADER + "".join(rows)


def test_a_session_gets_one_row_per_structure_and_width_and_old_bytes_stay_a_prefix(tmp_path):
    path = margins_file(tmp_path, done_before(DAY))
    before = path.read_bytes()
    assert make_job(path, {DAY: span_zip()}).run() == 0
    after = path.read_bytes()
    assert after.startswith(before)
    new = after[len(before) :].decode().splitlines()
    assert len(new) == 6 and new[0].startswith(
        "SF,100,1950.00,-10725.00,52000.00,NSE SPAN nsccl.20261014.i1.zip sha256="
    )
    assert all(line.endswith(",2026-10-14") for line in new)


def test_a_second_run_changes_nothing(tmp_path):
    path = margins_file(tmp_path, done_before(DAY))
    make_job(path, {DAY: span_zip()}).run()
    once = path.read_bytes()
    alerts = Alerts()
    assert make_job(path, {DAY: span_zip()}, alerts=alerts).run() == 0
    assert path.read_bytes() == once and alerts.sent == []


@pytest.mark.parametrize("created", ["202610140900", "202610141532", "202610150100"])
def test_a_file_written_at_or_after_9_am_on_its_day_writes_no_row(tmp_path, created):
    path, alerts = margins_file(tmp_path, done_before(DAY)), Alerts()
    before = path.read_bytes()
    assert make_job(path, {DAY: span_zip(created=created)}, alerts=alerts).run() == 1
    assert path.read_bytes() == before
    assert len(alerts.sent) == 1 and "not before 09:00" in alerts.sent[0]


def test_a_file_written_just_before_9_am_is_used(tmp_path):
    path = margins_file(tmp_path, done_before(DAY))
    assert make_job(path, {DAY: span_zip(created="202610140859")}).run() == 0


@pytest.mark.parametrize("data, cause", [(None, "not archived in Drive"), (b"junk", "not a readable zip"),
                                         (span_zip(som="5"), "short-option minimum")],
                         ids=["missing", "damaged", "unmodelled"])  # fmt: skip
def test_a_missing_or_invalid_file_writes_nothing_and_alerts_once(tmp_path, data, cause):
    path, alerts = margins_file(tmp_path, done_before(DAY)), Alerts()
    before = path.read_bytes()
    assert make_job(path, {DAY: data} if data else {}, alerts=alerts).run() == 1
    assert path.read_bytes() == before
    assert len(alerts.sent) == 1 and cause in alerts.sent[0] and "2026-10-14" in alerts.sent[0]


def test_a_drive_error_or_no_expiry_far_enough_out_is_alerted_not_a_crash(tmp_path):
    path, alerts = margins_file(tmp_path, done_before(DAY)), Alerts()
    job = make_job(path, {DAY: span_zip(futures=(date(2026, 10, 27),))}, alerts=alerts)
    assert job.run() == 1 and "no monthly expiry" in alerts.sent[0]

    def refused(day):
        raise ConnectionError("Drive said no")

    job.day_file = refused
    assert job.run() == 1 and "the Drive read failed (ConnectionError: Drive said no)" in alerts.sent[1]


def test_every_pending_day_is_tried_and_all_problems_go_in_one_alert(tmp_path):
    path, alerts = margins_file(tmp_path), Alerts()
    assert make_job(path, {DAY: span_zip()}, alerts=alerts).run() == 1
    assert "2026-10-14" in path.read_text()  # the good day is written
    assert len(alerts.sent) == 1 and alerts.sent[0].count("not archived in Drive") == 5  # 7-13 Oct, weekdays


def test_a_different_figure_for_an_existing_row_is_refused_and_nothing_is_written(tmp_path):
    clash = "SC,200,1.00,0,0,hand entry,2026-10-14\n"
    path, alerts = margins_file(tmp_path, done_before(DAY) + clash), Alerts()
    before = path.read_bytes()
    assert make_job(path, {DAY: span_zip()}, alerts=alerts).run() == 1
    assert path.read_bytes() == before and "different row" in alerts.sent[0]


def test_the_log_refuses_a_wrong_header_or_a_missing_file(tmp_path):
    with pytest.raises(MarginLogConflict, match="missing"):
        margin_log(tmp_path / "none.csv").append([])
    with pytest.raises(MarginLogConflict, match="columns"):
        margin_log(margins_file(tmp_path, "structure,width\n")).append([])


def test_a_file_without_a_final_newline_is_refused_by_name_and_left_as_it_was(tmp_path):
    """O9b step 2: the log appends through the RowLog port, which refuses a table it cannot extend without changing its
    last row (a hand-edited file); a Drive series is write-once parts, so this cannot happen there."""
    path = margins_file(tmp_path, HEADER + "SF,100,1.00,0,0,x,2026-10-01")
    before = path.read_bytes()
    with pytest.raises(MarginLogConflict, match="does not end with a new line"):
        margin_log(path).append([MarginRow("SF", 100.0, MarginFigure(2.0, -1.0, 3.0), "y", DAY)])
    assert path.read_bytes() == before


@pytest.mark.parametrize("now, due", [
    (datetime(2026, 10, 14, 7, 45, tzinfo=IST), date(2026, 10, 14)),
    (datetime(2026, 10, 13, 23, 0, tzinfo=IST), date(2026, 10, 13)),  # an evening run never races NSE's file
    (datetime(2026, 10, 17, 9, 0, tzinfo=IST), date(2026, 10, 19)),  # Saturday: Monday's file
])  # fmt: skip
def test_the_due_session_is_the_first_from_today_on(now, due):
    assert due_session(now, weekday) == due


def test_a_calendar_without_sessions_is_an_alert_not_a_hang(tmp_path):
    alerts = Alerts()
    job = make_job(margins_file(tmp_path), {}, alerts=alerts)
    job.is_trading_day = lambda day: False
    assert job.run() == 1 and "no session within" in alerts.sent[0]


def test_c2_uses_a_computed_row_from_its_day_on_and_never_before(tmp_path):
    path = margins_file(tmp_path, done_before(DAY))
    make_job(path, {DAY: span_zip()}).run()
    table, terms = (
        MarginTable(FileTable(path), DaysOld(7), 65),
        TradeTerms("SF", 200.0, lots=2),
    )  # width 200: no older row
    # sold C20000 and P20000, bought C20200 and P19800 at 10: scan max(100 - 20, -15 + 90) = 80 a unit, NOV -210
    assert table.parts(terms, DAY) == MarginParts(80 * 65.0, -210 * 65.0, 52000.0, "SF width 200")
    assert table.margin(terms, DAY) == pytest.approx(2 * (5200 + 52000))  # a credit: scan + exposure (judge 75)
    with pytest.raises(RiskInputError, match="no margin recorded"):
        table.margin(terms, DAY - timedelta(days=1))  # the day before: the row is not visible yet
    assert table.margin(terms, DAY + timedelta(days=7)) > 0
    with pytest.raises(RiskInputError, match="older than 7 days"):
        table.margin(terms, DAY + timedelta(days=8))


def test_the_created_cutoff_is_9_am_ist():
    from fno.constants import SPAN_BOD_CREATED_BEFORE

    assert time(9, 0) == SPAN_BOD_CREATED_BEFORE


def test_without_any_broker_check_rows_are_printed_and_none_written(tmp_path):
    path, alerts, printed = margins_file(tmp_path, done_before(DAY)), Alerts(), []
    before = path.read_bytes()
    assert make_job(path, {DAY: span_zip()}, alerts=alerts, check=BrokerApprovals({}), printed=printed).run() == 1
    assert path.read_bytes() == before
    assert any(line.startswith("SF,100,1950.00,-10725.00,52000.00,NSE SPAN") for line in printed)
    assert len(alerts.sent) == 1 and "6 rows computed, none written" in alerts.sent[0]
    assert "risk.margins.nse_span_check" in alerts.sent[0]


def test_the_repository_config_records_the_groww_check_and_not_before_its_day():
    from fno.config import load_app_config

    check = BrokerApprovals.from_margins_block(load_app_config()["risk"]["margins"])
    groww = Approval("Groww margin API (read-only), orchestrator run", date(2026, 10, 14))  # response 77, check 2
    assert dict(check.by_code) == {"SF": groww, "SC": groww, "BF": groww}  # story STR1b: no new code has a date
    assert check.approves("SF", date(2026, 10, 14)) and not check.approves("SF", date(2026, 10, 13))


def test_the_first_run_after_the_check_writes_from_its_day_and_does_not_alert_on_the_days_before(tmp_path):
    """The real first run (judge 77's check passed 14 Oct, nothing written yet): 7-13 Oct can never get a row, so they
    are not pending; alerting on them would fail every run until they leave the 7-day window."""
    path, alerts = margins_file(tmp_path), Alerts()
    check = BrokerApprovals({code: Approval("check", DAY) for code in ("SF", "SC", "BF")})
    files = {DAY - timedelta(days=n): span_zip() for n in range(8)}
    job = make_job(path, files, alerts=alerts, check=check)
    assert job.pending_days(DAY) == [DAY]
    assert job.run() == 0 and alerts.sent == []
    assert {line.rsplit(",", 1)[1] for line in path.read_text().splitlines()[1:]} == {DAY.isoformat()}


@pytest.mark.parametrize("late_hours", [0, 5])
def test_the_main_cron_runs_on_the_session_s_own_ist_date_even_5_hours_late(late_hours):
    """nse-margins.yml's first cron is 22:00 UTC, the previous UTC day (GitHub started this repository's morning crons
    4-5 h late, 14-16 Oct 2026): at 03:30 IST, or 08:30 IST if late, the due session is that IST day's, before 09:15."""
    workflow = yaml.safe_load((ROOT / ".github/workflows/nse-margins.yml").read_text(encoding="utf-8"))
    minute, hour = (int(f) for f in workflow[True]["schedule"][0]["cron"].split()[:2])
    start = datetime(2026, 10, 15, hour, minute, tzinfo=UTC) + timedelta(hours=late_hours)
    now = start.astimezone(IST)
    assert now.time() < time(9, 15) and now.date() == date(2026, 10, 16)
    assert due_session(now, weekday) == date(2026, 10, 16)
