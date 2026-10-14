"""Story E3 end to end over 5 simulated days with fakes at the seams (test plan): a normal day, a slow book, a failed
execution snapshot, a holiday and a restart after the fills. E4's desks, C3's data gate, the capture records and the
run log are the real ones; the run's commits are checked in timetable order (decisions before the snapshot, the
snapshot before the fills)."""

import json
from datetime import date

import pytest

from fno.books.account import PaperAccount
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, NO_DECISION_LATE, OUTCOME_CLOSED, OUTCOME_OPENED
from fno.desk.daily_ports import CommittedDecision
from fno.desk.daily_steps import NO_SNAPSHOT
from fno.desk.exit_rules import TimeExit
from fno.desk.records import DeskRecords
from tests.desk.builders import at, fly_order

from .fakes import C4, Decisions, Rules, daily_run

NORMAL, SLOW, FAILED, HOLIDAY, RESTART = (date(2026, 10, d) for d in (14, 15, 16, 20, 21))
BOOKS = (BOOK1_RULES, BOOK2_HYBRID)


def decided(book, trade_id, day, committed=(15, 5)):
    order = fly_order(trade_id, book=book, decided_at=at(15, 0, day=day))
    return CommittedDecision(book, f"{day}-r1", at(*committed, day=day), (order,))


def fills(root, book):
    return DeskRecords(PaperAccount(root, book)).fill_rows()


def events(root, book):
    return {(e["trade_id"], e["outcome"]) for e in DeskRecords(PaperAccount(root, book)).event_rows()}


@pytest.fixture
def week(root, tmp_path, alerts):
    decisions = Decisions()
    decisions.add(decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    decisions.add(decided(BOOK2_HYBRID, "b1", NORMAL, (15, 6)), NORMAL)
    decisions.add(decided(BOOK1_RULES, "t2", SLOW), SLOW)
    decisions.add(decided(BOOK2_HYBRID, "b2", SLOW, (15, 13)), SLOW)  # after the 15:12 deadline: the slow book
    decisions.add(decided(BOOK1_RULES, "t3", FAILED), FAILED)
    decisions.add(decided(BOOK1_RULES, "t4", RESTART), RESTART)
    rules = Rules({"t1": [TimeExit(11)]})  # 27 Oct expiry: due from 16 Oct, the failed-snapshot day
    run, clock, capture, commits = daily_run(root, tmp_path, alerts, BOOKS, decisions, C4(), rules)
    capture.incomplete.add(FAILED)
    return run, clock, capture, commits, rules


def run_day(run, clock, day):
    clock.now = at(14, 50, day=day)
    return run.run(day)


def test_five_days(root, week):
    run, clock, capture, commits, rules = week

    log = run_day(run, clock, NORMAL)  # criterion 2: every timely decision fills at one snapshot ID and hash
    snapshot = log.result("snapshot")
    assert snapshot["valid"] and log.result("fills")["t1"]["outcome"] == OUTCOME_OPENED
    assert {(r["snapshot_id"], r["snapshot_sha256"]) for b in BOOKS for r in fills(root, b)} == {
        (snapshot["snapshot_id"], snapshot["sha256"])}  # fmt: skip
    assert [m.split("step ")[-1] for _, m in commits.made if "step" in m] == [
        "versions", "pack", "decisions", "snapshot", "fills", "exits"]  # fmt: skip

    log = run_day(run, clock, SLOW)  # criterion 1: the slow book gets "no decision (late)"; the other fills on time
    assert log.result("decisions")[BOOK2_HYBRID]["decision"] == NO_DECISION_LATE
    late = root / "journal" / BOOK2_HYBRID / "decisions" / SLOW.isoformat() / "no_decision.json"
    assert json.loads(late.read_text())["kind"] == NO_DECISION_LATE and "b2" not in log.result("fills")
    assert log.result("fills")["t2"]["outcome"] == OUTCOME_OPENED
    assert log.steps["snapshot"]["started_at"] == at(15, 15, day=SLOW).isoformat()  # not delayed by the slow book

    log = run_day(run, clock, FAILED)  # criterion 3: one common retry, no new risk, exits still run
    assert log.result("snapshot")["valid"] is False and len(log.result("snapshot")["attempts"]) == 2
    assert log.result("fills")["t3"] == {"outcome": "not filled", "reason": NO_SNAPSHOT}
    assert ("t1", OUTCOME_CLOSED) in events(root, BOOK1_RULES)

    taken = len(capture.taken)  # criterion 4: a holiday runs nothing and fails nothing
    log = run_day(run, clock, HOLIDAY)
    assert list(log.steps) == ["skipped"] and len(capture.taken) == taken

    rules.crash_once = True  # criterion 5: killed after the fills, restarted the same day
    with pytest.raises(RuntimeError, match="killed after the fills"):
        run_day(run, clock, RESTART)
    before = (len(capture.taken), len(fills(root, BOOK1_RULES)))
    log = run.run(RESTART)  # the restart comes later the same day
    assert (len(capture.taken), len(fills(root, BOOK1_RULES))) == before and "exits" in log.steps
    assert list(log.steps) == ["versions", "pack", "decisions", "snapshot", "fills", "exits"]


def test_every_step_s_times_inputs_and_result_are_in_the_committed_run_file(root, week):
    """Criterion 6, and the judge's check of a week's run files: decisions before the snapshot before the fills."""
    run, clock, *_ = week
    for day in (NORMAL, SLOW, FAILED, HOLIDAY, RESTART):
        run_day(run, clock, day)
    for day in (NORMAL, SLOW, FAILED, RESTART):
        steps = json.loads((root / "journal" / "runs" / f"{day}.json").read_text())["steps"]
        assert all({"started_at", "finished_at", "inputs", "result"} <= set(s) for s in steps.values())
        moments = [steps[s]["started_at"] for s in ("decisions", "snapshot", "fills")]
        assert moments == sorted(moments) and steps["decisions"]["inputs"]["deadline"].endswith("15:12:00+05:30")


@pytest.mark.parametrize("failing", BOOKS)
def test_a_decision_without_a_completed_c4_pass_is_never_filled(root, tmp_path, alerts, failing):
    """Criterion 7, per book, through the `ValidityGate` seam (C4 is built apart)."""
    decisions = Decisions()
    decisions.add(decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    decisions.add(decided(BOOK2_HYBRID, "b1", NORMAL), NORMAL)
    validity = C4(failing=[failing])
    run, clock, *_ = daily_run(root, tmp_path, alerts, BOOKS, decisions, validity, Rules())
    log = run_day(run, clock, NORMAL)
    stopped, other = ("t1", "b1") if failing == BOOK1_RULES else ("b1", "t1")
    assert log.result("fills")[stopped]["reason"].startswith("not filled: no completed C4 pass")
    assert log.result("fills")[other]["outcome"] == OUTCOME_OPENED and sorted(validity.asked) == ["b1", "t1"]
    assert not fills(root, failing)


class Skewed(Decisions):
    """A source whose commit times run ahead of the desk's clock (another container's clock): it returns the decision
    whatever the deadline says."""

    def committed(self, book, day, deadline):
        return self.by_day[(book, day)][-1]


def test_a_decision_committed_after_the_snapshot_started_is_late_at_the_fill(root, tmp_path, alerts):
    """D3's rule again at the fill, against the snapshot actually taken: a decision whose commit time is not before
    the capture's start never fills, whatever the source said."""
    decisions = Skewed()
    decisions.add(decided(BOOK1_RULES, "t1", NORMAL, (15, 15, 10)), NORMAL)
    run, clock, *_ = daily_run(root, tmp_path, alerts, (BOOK1_RULES,), decisions, C4(), Rules())
    log = run_day(run, clock, NORMAL)
    assert log.result("fills")["t1"]["reason"].startswith("late: committed") and not fills(root, BOOK1_RULES)


def test_a_successful_common_retry_fills_every_book_at_the_retry_s_capture(root, tmp_path, alerts):
    decisions = Decisions()
    decisions.add(decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    decisions.add(decided(BOOK2_HYBRID, "b1", NORMAL), NORMAL)
    run, clock, capture, _ = daily_run(root, tmp_path, alerts, BOOKS, decisions, C4(), Rules())
    capture.incomplete_once.add(NORMAL)
    log = run_day(run, clock, NORMAL)
    first, retry = log.result("snapshot")["attempts"]
    assert log.result("snapshot")["valid"] and log.result("snapshot")["snapshot_id"] == retry != first
    assert {r["snapshot_id"] for b in BOOKS for r in fills(root, b)} == {retry}


def test_a_muhurat_only_evening_runs_nothing(root, tmp_path, alerts):
    run, clock, capture, commits = daily_run(root, tmp_path, alerts, BOOKS, Decisions(), C4(), Rules())
    log = run_day(run, clock, date(2026, 11, 8))  # Diwali: a muhurat session only (A7)
    assert list(log.steps) == ["skipped"] and log.steps["skipped"]["inputs"] == {"session": "muhurat"}
    assert capture.taken == [] and [m for _, m in commits.made] == ["Desk run 2026-11-08 step skipped"]


def test_a_step_is_never_recorded_twice(tmp_path):
    from fno.desk.run_log import RunLog

    log = RunLog.open(tmp_path, NORMAL)
    log.record("pack", at(14, 58), at(14, 59), {}, {"built": True})
    with pytest.raises(ValueError, match="never repeats a step"):
        RunLog.open(tmp_path, NORMAL).record("pack", at(15, 0), at(15, 1), {}, {"built": True})
