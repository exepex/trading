"""Story O11, the failures the recorded day can really have: each leaves its record (run log, decision record, failure
log) and, where the code alerts today, exactly the alert. The alerts O1's command steps will add are expected-missing
in test_expected_missing.py."""

import csv

import pytest

from fno.constants import BOOK1_RULES
from fno.desk.daily_ports import CommitFailed
from fno.desk.daily_run import RunStopped
from fno.desk.no_decision import NO_DECISION_LATE
from fno.forecast_v4_rules.capture import CaptureRefused
from fno.quotes.recorder import DATASET, RecordResult
from tests.desk.conftest import RecordingAlerts
from tests.timetable.fakes import Commits

from . import real_day as rd
from .replay import Replay


class WindowClosed:
    """The recorder's answer when the 15:15 capture cannot be made in its window: no snapshot ID."""

    def __init__(self, clock, store):
        pass

    def __call__(self):
        return RecordResult("window closed")


class RefusedCommits(Commits):
    """The run's committer refusing one step's commit (a push rejected every time)."""

    def __init__(self, clock, step: str):
        super().__init__(clock)
        self.step = step

    def commit(self, paths, message, own_unpushed=None):
        if message.endswith(f"step {self.step}"):
            raise CommitFailed("push rejected 3 times")
        return super().commit(paths, message, own_unpushed)


@pytest.fixture
def alerts():
    return RecordingAlerts()


def test_no_3pm_capture_no_pack_book1_refuses_and_the_book_has_a_no_decision_record(tmp_path, monkeypatch, alerts):
    replay = Replay(tmp_path, monkeypatch, alerts)
    canonical = tmp_path / rd.QUOTES / DATASET / "2026" / "10" / "nifty_20261016.canonical"
    canonical.unlink()
    refused = []
    decide = replay.clock.decide
    replay.clock.decide = lambda day: refused.append(_raised(decide, day)) or None
    log = replay.daily_run().run(rd.DAY)
    assert log.result("pack")["built"] is False and "snapshot" in log.result("pack")["reason"]
    assert refused == ["InputsRefused: no common pack for 2026-10-16: Book 1 reads the packs (E2)"]
    assert log.result("decisions")[BOOK1_RULES]["decision"] == NO_DECISION_LATE
    assert (tmp_path / "journal" / BOOK1_RULES / "decisions" / "2026-10-16").is_dir()  # the no-decision record
    assert log.result("fills") == {}


def test_a_failed_execution_capture_is_alerted_recorded_and_fills_nothing(tmp_path, monkeypatch, alerts):
    out = Replay(tmp_path, monkeypatch, alerts, capture=WindowClosed).run()
    snapshot = out.log.result("snapshot")
    assert snapshot["valid"] is False and snapshot["attempts"] == [None, None]
    assert {r["outcome"] for r in out.log.result("fills").values()} == {"not filled"}
    assert alerts.sent == [
        "F&O paper desk 2026-10-16 (no capture): no new trade: stale or unverified data: snapshot: "
        "no execution capture is named for 2026-10-16"
    ]


def test_no_nse_file_blocks_the_trade_in_c4_with_its_failure_row_and_c3_alerts(tmp_path, monkeypatch, alerts):
    out = Replay(tmp_path, monkeypatch, alerts, listed=False).run()
    with open(tmp_path / "journal" / BOOK1_RULES / "validity_failures.csv", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert [(r["day"], r["check"]) for r in rows] == [("2026-10-16", "listing")]
    assert rows[0]["reason"] == "no NSE F&O file in the 7 days before 2026-10-16"
    assert out.log.result("fills") == {} and out.scorecards == []
    (sent,) = alerts.sent
    assert "no new trade" in sent and "NSE's file of the previous session 2026-10-15 is not archived" in sent


def test_a_failed_commit_stops_the_run_with_one_alert(tmp_path, monkeypatch, alerts):
    replay = Replay(tmp_path, monkeypatch, alerts)
    replay.run_commits = RefusedCommits(replay.clock, "fills")
    with pytest.raises(RunStopped) as stopped:
        replay.daily_run().run(rd.DAY)
    assert alerts.sent == [str(stopped.value)] and "fills" in alerts.sent[0]


def test_forecasts_after_the_1430_cutoff_are_refused_and_write_nothing(tmp_path, monkeypatch, alerts):
    replay = Replay(tmp_path, monkeypatch, alerts, forecast_time=rd.at(14, 31))
    with pytest.raises(CaptureRefused):
        replay.forecast()
    assert not [*tmp_path.glob("weather/**/*.json")] and not [*tmp_path.glob("v4/**/*.csv")]


def _raised(action, *args) -> str:
    try:
        action(*args)
    except Exception as refused:  # what O1's command step would record and alert (expected-missing)
        return f"{type(refused).__name__}: {refused}"
    return "no refusal"
