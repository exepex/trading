"""Story O11, the failures the recorded day can really have: each leaves its record (run log, decision record, failure
log) and its alert, through O1's run: a refused or failed O1 step is recorded and alerted once, and the run goes on."""

import csv

import pytest

from fno.constants import BOOK1_RULES, REVIEWS_STEP, STEP_FAILED, STEP_REFUSED
from fno.daily.steps import FAILED_ALERT
from fno.desk.daily_ports import CommitFailed
from fno.desk.daily_run import RunStopped
from fno.desk.no_decision import NO_DECISION_LATE
from fno.quotes.recorder import DATASET, RecordResult
from tests.desk.conftest import RecordingAlerts
from tests.timetable.fakes import Commits

from . import real_day as rd
from .replay import Replay

SNAPSHOT_ALERT = (
    "F&O paper desk 2026-10-16 (no capture): no new trade: stale or unverified data: snapshot: no execution capture is "
    "named for 2026-10-16"
)


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


def step_alert(name: str, status: str, reason: str) -> str:
    return FAILED_ALERT.format(day=rd.DAY, name=name, status=status, reason=reason, note="")


def test_no_3pm_capture_no_pack_book1_fails_alerted_and_the_book_has_a_no_decision_record(tmp_path, monkeypatch,
                                                                                        alerts):  # fmt: skip
    replay = Replay(tmp_path, monkeypatch, alerts)
    (tmp_path / rd.QUOTES / DATASET / "2026" / "10" / "nifty_20261016.canonical").unlink()
    log = replay.run().log
    assert log.result("pack")["built"] is False and "snapshot" in log.result("pack")["reason"]
    why = "InputsRefused: no common pack for 2026-10-16: Book 1 reads the packs (E2)"
    assert log.result("book1") == {"status": STEP_FAILED, "reason": why}
    assert step_alert("book1", STEP_FAILED, why) in alerts.sent
    assert log.result("decisions")[BOOK1_RULES]["decision"] == NO_DECISION_LATE
    assert (tmp_path / "journal" / BOOK1_RULES / "decisions" / "2026-10-16").is_dir()  # the no-decision record
    assert log.result("fills") == {} and log.result(REVIEWS_STEP)["status"] == "ok"  # the run went on


def test_a_failed_execution_capture_is_alerted_recorded_and_fills_nothing(tmp_path, monkeypatch, alerts):
    out = Replay(tmp_path, monkeypatch, alerts, capture=WindowClosed).run()
    snapshot = out.log.result("snapshot")
    assert snapshot["valid"] is False and snapshot["attempts"] == [None, None]
    assert {r["outcome"] for r in out.log.result("fills").values()} == {"not filled"}
    assert alerts.sent == [SNAPSHOT_ALERT]


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
        replay.run()
    assert alerts.sent == [str(stopped.value)] and "fills" in alerts.sent[0]


def test_at_todays_1433_start_both_forecast_steps_are_refused_alerted_and_write_nothing(tmp_path, monkeypatch,
                                                                                      alerts):  # fmt: skip
    """The routine's stored start (CLAUDE.md) is after G10's 14:30 cutoff: today no live forecast can be made."""
    log = Replay(tmp_path, monkeypatch, alerts, start=rd.at(14, 33)).run().log
    for name in ("weather", "forecasts_v4"):
        result = log.result(name)
        assert result["status"] == STEP_REFUSED and "14:30 cutoff" in result["reason"]
        assert step_alert(name, STEP_REFUSED, result["reason"]) in alerts.sent
    assert not [*tmp_path.glob("weather/**/*.json")] and not [*tmp_path.glob("v4/**/*.csv")]
    assert log.result("fills")  # the desk's day goes on


def test_an_owner_override_in_the_decision_is_refused_alerted_and_nothing_trades(tmp_path, monkeypatch, alerts):
    """D3 merged (DESK_DECISIONS row 229 item 4): no paper decision carries an owner override."""
    log = Replay(tmp_path, monkeypatch, alerts, context={"owner_override": "owner says trade"}).run().log
    result = log.result("book1")
    assert result["status"] == STEP_FAILED and "the owner never overrides a paper decision" in result["reason"]
    assert step_alert("book1", STEP_FAILED, result["reason"]) in alerts.sent
    assert log.result("decisions")[BOOK1_RULES]["decision"] == NO_DECISION_LATE and log.result("fills") == {}
