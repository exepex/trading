"""Story A14: the daily job appends each session's rows once, point in time, and fails closed with one alert."""

from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

from fno.models import IST
from fno.nse_margins.calculator import NseIndexOptionExposure, SpanMarginCalculator
from fno.nse_margins.job import NseMarginJob, due_session
from fno.nse_margins.margin_log import MarginLog, MarginLogConflict
from fno.nse_margins.rows import MarginRow, MarginRowBuilder
from fno.research_engine.structures import LongIronFly, ShortCondor, ShortIronFly
from fno.risk.inputs import RiskInputError, TradeTerms
from fno.risk.margins import MarginTable

from .span_builder import DAY, LOT, span_zip

HEADER = "structure,width,margin_per_lot_rs,source,as_of\n"
MORNING = datetime(2026, 10, 14, 7, 45, tzinfo=IST)


def weekday(day: date) -> bool:
    return day.weekday() < 5


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text: str) -> str:
        self.sent.append(text)
        return "alert sent"


def margins_file(tmp_path: Path, text: str = HEADER) -> Path:
    path = tmp_path / "margins.csv"
    path.write_text(text, encoding="utf-8")
    return path


def make_job(path: Path, files: dict[date, bytes], now: datetime = MORNING, alerts: Alerts | None = None):
    builder = MarginRowBuilder((ShortIronFly(), ShortCondor(), LongIronFly()), (100.0, 200.0),
                               SpanMarginCalculator(NseIndexOptionExposure(), LOT), 30)  # fmt: skip
    day_file = lambda day: (f"nsccl.{day:%Y%m%d}.i1.zip", files.get(day))  # noqa: E731
    return NseMarginJob(day_file, builder, MarginLog(path), weekday, alerts or Alerts(), lambda: now, lambda _: None)


def done_before(day: date) -> str:
    """Rows for the week before `day`, so only `day` is pending."""
    rows = [f"SF,100,1.00,NSE SPAN old sha256=00,{day - timedelta(days=n)}\n" for n in range(1, 8)]
    return HEADER + "".join(rows)


def test_a_session_gets_one_row_per_structure_and_width_and_old_bytes_stay_a_prefix(tmp_path):
    path = margins_file(tmp_path, done_before(DAY))
    before = path.read_bytes()
    assert make_job(path, {DAY: span_zip()}).run() == 0
    after = path.read_bytes()
    assert after.startswith(before)
    new = after[len(before) :].decode().splitlines()
    assert len(new) == 6 and new[0].startswith("SF,100,53950.00,NSE SPAN nsccl.20261014.i1.zip sha256=")
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
    clash = "SC,200,1.00,hand entry,2026-10-14\n"
    path, alerts = margins_file(tmp_path, done_before(DAY) + clash), Alerts()
    before = path.read_bytes()
    assert make_job(path, {DAY: span_zip()}, alerts=alerts).run() == 1
    assert path.read_bytes() == before and "different row" in alerts.sent[0]


def test_the_log_refuses_a_wrong_header_or_a_missing_file(tmp_path):
    with pytest.raises(MarginLogConflict, match="missing"):
        MarginLog(tmp_path / "none.csv").append([])
    with pytest.raises(MarginLogConflict, match="columns"):
        MarginLog(margins_file(tmp_path, "structure,width\n")).append([])


def test_a_file_without_a_final_newline_gets_one_before_the_new_rows(tmp_path):
    path = margins_file(tmp_path, HEADER + "SF,100,1.00,x,2026-10-01")
    MarginLog(path).append([MarginRow("SF", 100.0, 2.0, "y", DAY)])
    assert path.read_text().splitlines()[-2:] == ["SF,100,1.00,x,2026-10-01", "SF,100,2.00,y,2026-10-14"]


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
    table, terms = MarginTable(path, max_age_days=7), TradeTerms("SF", 200.0, lots=2)
    assert table.margin(terms, DAY) == pytest.approx(2 * float(_row(path, "SF", "200", DAY)))
    with pytest.raises(RiskInputError, match="no margin recorded"):
        table.margin(terms, DAY - timedelta(days=1))  # the day before: the row is not visible yet
    assert table.margin(terms, DAY + timedelta(days=7)) > 0
    with pytest.raises(RiskInputError, match="older than 7 days"):
        table.margin(terms, DAY + timedelta(days=8))


def _row(path: Path, structure: str, width: str, day: date) -> str:
    for line in path.read_text().splitlines():
        parts = line.split(",")
        if parts[0] == structure and parts[1] == width and parts[-1] == day.isoformat():
            return parts[2]
    raise AssertionError("row not found")


def test_the_created_cutoff_is_9_am_ist():
    from fno.constants import SPAN_BOD_CREATED_BEFORE

    assert time(9, 0) == SPAN_BOD_CREATED_BEFORE
