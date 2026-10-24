"""Owner, 24 Oct ("1 - A"), after judges 569.2 SF3 and 570.2 finding 1: a failed fills step is final for the day (no
new trade on a rerun, fail closed, the alert says so), and no fills step starts after `fills_by`, a rerun after a
stopped run included (decision 47). Judge 570.2's minor: the written count leaves out a blocked book."""

from datetime import timedelta

import pytest

from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI, OUTCOME_OPENED, STEP_FAILED, STEP_REFUSED
from fno.desk.daily_run import FILLS_LATE, FILLS_REFUSED, NOT_RETRIED, RERUN_FINAL, WRITTEN, RunStopped
from fno.desk.run_log import RETRY
from tests.desk.builders import at

from .fakes import C4, Decisions, LocalSync, Rules, daily_run
from .test_daily_run import NORMAL, decided, fills, run_day
from .test_failed_step_retry import TIMEOUT, CommitFailing, FailingSync, ledger

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


def stopped_at_the_fills(root, tmp_path, alerts):
    """Decision 47's case: book 2's account commit fails, so the run stops inside the fills and logs no fills step;
    book 1's trade was already written."""
    run, clock = run_for(root, tmp_path, alerts, (BOOK1_RULES, BOOK2_HYBRID))
    run.steps.sync = CommitFailing(root, BOOK2_HYBRID)
    with pytest.raises(RunStopped, match="run STOPPED at step fills"):
        run_day(run, clock, NORMAL)
    run.steps.sync = LocalSync(root)
    return run, clock


@pytest.mark.parametrize("seconds", [0, 59])
def test_a_rerun_after_a_stop_fills_up_to_the_end_of_the_fills_by_minute(root, tmp_path, alerts, seconds):
    run, clock = stopped_at_the_fills(root, tmp_path, alerts)
    clock.now = at(15, 20, day=NORMAL) + timedelta(seconds=seconds)  # good and boundary: inside 15:20
    log = run.run(NORMAL)
    assert log.result("fills")["b1"]["outcome"] == OUTCOME_OPENED and fills(root, BOOK2_HYBRID)
    assert not [t for t in alerts.sent if "step fills REFUSED" in t]


@pytest.mark.parametrize("minutes", [1, 8 * 60 + 30])
def test_a_rerun_after_a_stop_past_fills_by_is_refused_and_opens_nothing(root, tmp_path, alerts, minutes):
    """Bad: one minute past 15:20 (15:21:00), and the judges' 23:50 probe. Book 1's trade, written before the stop,
    stays; book 2 opens nothing; one alert; a later rerun never runs the fills either."""
    run, clock = stopped_at_the_fills(root, tmp_path, alerts)
    opened = fills(root, BOOK1_RULES)
    clock.now = at(15, 20, day=NORMAL) + timedelta(minutes=minutes)
    log = run.run(NORMAL)
    reason = FILLS_LATE.format(now=clock.now, by=at(15, 20, day=NORMAL))
    assert log.result("fills") == {"status": STEP_REFUSED, "reason": reason} and log.done("fills")
    assert not fills(root, BOOK2_HYBRID) and fills(root, BOOK1_RULES) == opened
    assert FILLS_REFUSED.format(day=NORMAL, reason=reason) in alerts.sent
    assert "exits" in log.steps and "trade_marks" in log.steps
    clock.now = clock.now.replace(hour=15, minute=19)  # even a clock set back: the refusal is recorded for the day
    assert run.run(NORMAL).result("fills")["status"] == STEP_REFUSED and not fills(root, BOOK2_HYBRID)


def test_a_first_run_whose_fills_start_past_fills_by_is_refused(root, tmp_path, alerts):
    """Empty case of a late day: the snapshot step ended past the minute (as on 22 Oct, 15:21:23); nothing fills."""
    run, clock = run_for(root, tmp_path, alerts, (BOOK1_RULES,))
    real = run.steps.take_snapshot

    def slow_snapshot(day):
        outcome = real(day)
        clock.now = at(15, 21, day=day)
        return outcome

    run.steps.take_snapshot = slow_snapshot
    log = run_day(run, clock, NORMAL)
    assert log.result("fills")["status"] == STEP_REFUSED and not fills(root, BOOK1_RULES)
