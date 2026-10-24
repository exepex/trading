"""Owner, 24 Oct ("1 - A"), after judges 569.2 SF3 and 570.2 finding 1: a failed fills step is final for the day (no
new trade on a rerun, fail closed, the alert says so), and a run that did not take the day's snapshot itself (a rerun
after a stopped run, decision 47) starts no fills after `fills_by`. Judge 570.2's minor: the written count leaves out
a blocked book."""

from datetime import timedelta

import pytest

from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI, OUTCOME_OPENED, STEP_FAILED, STEP_REFUSED
from fno.desk.daily_ports import CommitFailed
from fno.desk.daily_run import FILLS_LATE, FILLS_REFUSED, NOT_RETRIED, RERUN_FINAL, WRITTEN, RunStopped
from fno.desk.run_log import RETRY
from tests.desk.builders import at

from .fakes import C4, Decisions, LocalSync, Rules, daily_run
from .test_daily_run import NORMAL, decided, fills, run_day
from .test_failed_step_retry import TIMEOUT, FailingSync, ledger

FINAL = RERUN_FINAL.format(why=NOT_RETRIED["fills"])


def run_for(root, tmp_path, alerts, books):
    decisions = Decisions()
    for book, trade in zip((BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI), ("t1", "b1", "c1"), strict=True):
        if book in books:
            decisions.add(*decided(book, trade, NORMAL), NORMAL)
    run, clock, *_ = daily_run(root, tmp_path, alerts, books, decisions, C4(), Rules())
    return run, clock


@pytest.mark.parametrize(("failing", "written"), [(BOOK1_RULES, 0), (BOOK2_HYBRID, 1)])
def test_a_failed_fills_step_is_final_and_a_rerun_opens_no_trade(root, tmp_path, alerts, failing, written):
    books = (BOOK1_RULES, BOOK2_HYBRID)
    run, clock = run_for(root, tmp_path, alerts, books)
    real, run.steps.sync = run.steps.sync, FailingSync(root, failing)
    log = run_day(run, clock, NORMAL)
    assert log.result("fills") == {"status": STEP_FAILED, "reason": TIMEOUT, RETRY: False} and log.done("fills")
    alert = next(t for t in alerts.sent if "step fills FAILED" in t)
    assert (WRITTEN.format(count=written) in alert) is bool(written) and alert.endswith(FINAL)
    assert "exits" in log.steps  # the risk-reducing steps still ran after it
    before = {book: (fills(root, book), ledger(root, book)) for book in books}

    run.steps.sync = real  # the cause gone, the owner's rerun the same day
    log = run.run(NORMAL)
    assert log.result("fills")[RETRY] is False and not fills(root, failing)  # the failing book opened nothing
    assert {book: (fills(root, book), ledger(root, book)) for book in books} == before


def test_the_written_count_leaves_out_a_blocked_book(root, tmp_path, alerts):
    """Judge 570.2 (plant J6): a blocked book's "not filled" entry is in the result but was never written."""
    run, clock = run_for(root, tmp_path, alerts, (BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI))
    run._unreviewed = lambda day: {BOOK1_RULES: "planted: last session's exits not reviewed"}
    run.steps.sync = FailingSync(root, BOOK3_AI)
    log = run_day(run, clock, NORMAL)
    assert log.result("fills")["status"] == STEP_FAILED and fills(root, BOOK2_HYBRID) and not fills(root, BOOK1_RULES)
    alert = next(t for t in alerts.sent if "step fills FAILED" in t)
    assert WRITTEN.format(count=1) in alert


class WrittenThenCommitFailing(LocalSync):
    """As `DriveAccountSync` does: `book`'s trade is written to its account, then its totals' commit fails."""

    def __init__(self, root, book):
        super().__init__(root)
        self.book = book

    def write(self, book, apply, message):
        result = super().write(book, apply, message)
        if book == self.book:
            raise CommitFailed("planted: the push was rejected every time")
        return result


def stopped_at_the_fills(root, tmp_path, alerts):
    """Decision 47's case: book 2's commit fails after its trade was written, so the run stops inside the fills and
    logs no fills step; a third book has not filled yet."""
    run, clock = run_for(root, tmp_path, alerts, (BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI))
    run.steps.sync = WrittenThenCommitFailing(root, BOOK2_HYBRID)
    with pytest.raises(RunStopped, match="run STOPPED at step fills"):
        run_day(run, clock, NORMAL)
    run.steps.sync = LocalSync(root)
    assert fills(root, BOOK1_RULES) and fills(root, BOOK2_HYBRID) and not fills(root, BOOK3_AI)
    return run, clock


def test_a_rerun_after_a_stop_at_fills_by_fills_the_rest_once(root, tmp_path, alerts):
    """Good and boundary: the rerun starts the fills at 15:20:00, the limit itself."""
    run, clock = stopped_at_the_fills(root, tmp_path, alerts)
    written = fills(root, BOOK2_HYBRID)
    clock.now = at(15, 20, day=NORMAL)
    log = run.run(NORMAL)
    assert log.result("fills")["c1"]["outcome"] == OUTCOME_OPENED and fills(root, BOOK3_AI)
    assert fills(root, BOOK2_HYBRID) == written  # replayed, never doubled
    assert not [t for t in alerts.sent if "step fills REFUSED" in t]


@pytest.mark.parametrize("seconds", [1, 60, (8 * 60 + 30) * 60])
def test_a_rerun_after_a_stop_past_fills_by_is_refused_and_opens_nothing(root, tmp_path, alerts, seconds):
    """Bad: one second and one minute past 15:20, and the judges' 23:50 probe. The trades written before the stop
    stay (and the alert says so); book 3 opens nothing; a later rerun never runs the fills either."""
    run, clock = stopped_at_the_fills(root, tmp_path, alerts)
    written = {book: fills(root, book) for book in (BOOK1_RULES, BOOK2_HYBRID)}
    clock.now = at(15, 20, day=NORMAL) + timedelta(seconds=seconds)
    log = run.run(NORMAL)
    reason = FILLS_LATE.format(now=clock.now, by=at(15, 20, day=NORMAL))
    assert log.result("fills") == {"status": STEP_REFUSED, "reason": reason} and log.done("fills")
    assert not fills(root, BOOK3_AI) and {book: fills(root, book) for book in written} == written
    assert FILLS_REFUSED.format(day=NORMAL, reason=reason) in alerts.sent and "stay in their accounts" in reason
    assert all(log.result(name).get("status") not in (STEP_FAILED, STEP_REFUSED) for name in ("exits", "trade_marks"))
    clock.now = clock.now.replace(hour=15, minute=19)  # even a clock set back: the refusal is recorded for the day
    assert run.run(NORMAL).result("fills")["status"] == STEP_REFUSED and not fills(root, BOOK3_AI)


def test_the_run_that_took_the_snapshot_fills_even_when_its_commit_ends_past_fills_by(root, tmp_path, alerts):
    """No person's choice comes between that snapshot and its fills (the reviewer's case: a slow push of the snapshot
    step), so a valid day is never lost to the limit."""
    run, clock = run_for(root, tmp_path, alerts, (BOOK1_RULES,))
    real = run.steps.take_snapshot

    def slow_commit(day):
        outcome = real(day)
        clock.now = at(15, 22, day=day)
        return outcome

    run.steps.take_snapshot = slow_commit
    log = run_day(run, clock, NORMAL)
    assert log.result("snapshot")["valid"] and log.result("fills")["t1"]["outcome"] == OUTCOME_OPENED
