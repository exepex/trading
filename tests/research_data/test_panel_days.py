"""Story A13's daily job: it appends only under a frozen protocol, checks each day's closes against O6's warm-up
closes, stops at the first failing session (keeping the days before it) and posts one line. Real 2024 subsets of NSE
files (panel_fixtures.py)."""

import json
from datetime import date, datetime

import pytest
from panel_fixtures import FixtureCalendar, build, inputs, panel_rows

from fno.forecast.freeze import NotFrozen
from fno.forecast.freeze_v2 import NotYetFrozen
from fno.models import IST
from fno.pipeline.panel_days import PanelDayJob
from fno.research_data.nifty_panel import NiftyPanelBuilder
from fno.research_data.panel_append import PanelAppender
from fno.research_data.panel_store import MANIFEST_FILE, WARMUP_FILE
from fno.storage.wiring import build_file_exceptions
from tests.pipeline.fakes import RecordingAlerts

FIRST, SECOND, NO_FILE = date(2024, 1, 2), date(2024, 3, 2), date(2024, 3, 4)
CALENDAR = FixtureCalendar({FIRST: "regular", SECOND: "special", NO_FILE: "regular"})
WARMUP_HEADER = "date,session,underlying,vix,index_file,index_sha256\n"
RUN_TIME = lambda: datetime(2024, 3, 2, 21, 41, tzinfo=IST)  # noqa: E731


def _second_day_closes(tmp_path) -> tuple[str, str]:
    build(tmp_path / "reference", SECOND, calendar=CALENDAR)
    row = panel_rows(tmp_path / "reference", 2024)[0]
    return row["underlying"], row["vix"]


@pytest.fixture
def panel(tmp_path):
    folder = tmp_path / "panel"
    build(folder, FIRST, calendar=CALENDAR)
    nifty, vix = _second_day_closes(tmp_path)
    (folder / WARMUP_FILE).write_text(WARMUP_HEADER + f"2024-03-02,special,{nifty},{vix},f,{'0' * 64}\n")
    return folder


def _job(folder, alerts, freeze_check=lambda: None):
    fo, index = inputs()
    builder = NiftyPanelBuilder(fo, index, CALENDAR, build_file_exceptions())
    return PanelDayJob(builder, PanelAppender(folder), CALENDAR, freeze_check, alerts, RUN_TIME, lambda line: None)


def _days(folder) -> list[str]:
    return sorted(json.loads((folder / MANIFEST_FILE).read_text())["days"])


def test_new_sessions_are_appended_once(panel):
    alerts = RecordingAlerts()
    assert _job(panel, alerts).run(SECOND) == 0
    assert _days(panel) == ["2024-01-02", "2024-03-02"]
    before = {p.name: p.read_bytes() for p in panel.iterdir()}
    assert _job(panel, alerts).run(SECOND) == 0  # nothing new: no file changes
    assert {p.name: p.read_bytes() for p in panel.iterdir()} == before and alerts.lines == []


def test_before_the_v3_freeze_nothing_is_appended_and_nothing_alerts(panel):
    def not_yet():
        raise NotYetFrozen("research/forecasts/FREEZE_v3.md does not exist")

    alerts = RecordingAlerts()
    assert _job(panel, alerts, not_yet).run(SECOND) == 0
    assert _days(panel) == ["2024-01-02"] and alerts.lines == []


def test_a_failed_freeze_check_appends_nothing_and_alerts(panel):
    def changed():
        raise NotFrozen("frozen files changed after the freeze: fno/research_data/panel_append.py")

    alerts = RecordingAlerts()
    assert _job(panel, alerts, changed).run(SECOND) == 1
    assert _days(panel) == ["2024-01-02"] and "freeze check failed" in alerts.lines[0]


def test_a_session_without_its_file_stops_keeps_the_earlier_days_and_alerts(panel):
    alerts = RecordingAlerts()
    assert _job(panel, alerts).run(NO_FILE) == 1
    assert _days(panel) == ["2024-01-02", "2024-03-02"]  # never jumps over a missing session
    assert len(alerts.lines) == 1 and "stopped at 2024-03-04" in alerts.lines[0]


def test_closes_that_differ_from_the_warmup_closes_stop_the_day(panel):
    (panel / WARMUP_FILE).write_text(WARMUP_HEADER + f"2024-03-02,special,1.00,1.00,f,{'0' * 64}\n")
    alerts = RecordingAlerts()
    assert _job(panel, alerts).run(SECOND) == 1
    assert _days(panel) == ["2024-01-02"] and "differ" in alerts.lines[0]


def test_a_day_without_its_warmup_close_waits_for_the_index_close_job(panel):
    (panel / WARMUP_FILE).write_text(WARMUP_HEADER)
    alerts = RecordingAlerts()
    assert _job(panel, alerts).run(SECOND) == 1
    assert _days(panel) == ["2024-01-02"] and "appends it first" in alerts.lines[0]


def test_the_real_job_writes_nothing_until_v3_is_frozen():
    from fno.pipeline.wiring import require_v3_frozen

    with pytest.raises(NotYetFrozen):  # no research/forecasts/FREEZE_v3.md yet (response 68 awaits review)
        require_v3_frozen()
