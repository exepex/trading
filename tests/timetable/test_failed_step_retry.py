"""DRY2 SF1 (orchestrator, 24 Oct 06:24): a desk step failed by an unexpected error is recorded failed and retried by a
same-day rerun when it is safe to repeat (the exits and the marks; never the fills, owner 24 Oct: see
test_fills_final.py); the retry doubles no fill, exit or ledger row, and a step that finished is never repeated."""

from datetime import date, timedelta

import pytest

from fno.books.account import PaperAccount
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, OUTCOME_CLOSED, STEP_FAILED
from fno.desk.daily_ports import CommitFailed
from fno.desk.daily_run import RERUN_RETRIES, RunStopped
from fno.desk.exit_rules import TimeExit
from fno.desk.run_log import RETRY

from .fakes import C4, Decisions, LocalSync, Rules, daily_run
from .test_daily_run import NORMAL, decided, events, fills, run_day

DUE = date(2026, 10, 16)  # t1's time exit (11 days before its 27 Oct expiry) is due from this session
TIMEOUT = "TimeoutError: planted: the Drive read timed out"


def ledger(root, book):
    return PaperAccount(root, book).ledger_rows()


def trade_open_on_normal(root, tmp_path, alerts, books=(BOOK1_RULES,)):
    decisions = Decisions()
    decisions.add(*decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    if BOOK2_HYBRID in books:
        decisions.add(*decided(BOOK2_HYBRID, "b1", NORMAL), NORMAL)
    run, clock, capture, commits = daily_run(
        root, tmp_path, alerts, books, decisions, C4(), Rules({"t1": [TimeExit(11)]})
    )
    return run, clock, capture, commits


class Flaky:
    """The real step, failing on the first `times` calls: after its writes (`after=True`) or before them."""

    def __init__(self, real, times=1, after=True):
        self.real, self.times, self.after, self.calls = real, times, after, 0

    def __call__(self, day):
        self.calls += 1
        if self.calls <= self.times:
            if self.after:
                self.real(day)
            raise TimeoutError("planted: the Drive read timed out\nsecond line")
        return self.real(day)


def test_a_rerun_after_an_exits_failure_runs_the_exits_again_with_nothing_doubled(root, tmp_path, alerts):
    run, clock, *_ = trade_open_on_normal(root, tmp_path, alerts)
    run_day(run, clock, NORMAL)
    flaky = Flaky(run.steps.review_exits, times=2)  # the first run writes every exit, then fails; so does the second
    run.steps.review_exits = flaky
    log = run_day(run, clock, DUE)
    assert log.result("exits") == {"status": STEP_FAILED, "reason": TIMEOUT, RETRY: True}
    assert ("t1", OUTCOME_CLOSED) in events(root, BOOK1_RULES)  # written before the planted error
    closed = (fills(root, BOOK1_RULES), ledger(root, BOOK1_RULES), events(root, BOOK1_RULES))
    assert [t for t in alerts.sent if "step exits FAILED" in t and t.endswith(RERUN_RETRIES)]
    assert not log.done("exits") and log.done("trade_marks")

    log = run.run(DUE)  # the owner's rerun the same day: the exits again, failing again (a step failing twice)
    assert log.result("exits")[RETRY] is True and flaky.calls == 2

    log = run.run(DUE)  # the third run: the exits review succeeds, every write a no-op
    assert flaky.calls == 3 and log.result("exits")[BOOK1_RULES]["reviewed"] is True
    assert (fills(root, BOOK1_RULES), ledger(root, BOOK1_RULES), events(root, BOOK1_RULES)) == closed
    assert list(log.steps)[-1] == "exits"  # the retried entry replaces the failed one, last in the order run

    run.run(DUE)  # a finished step is never repeated
    assert flaky.calls == 3


def test_an_exits_failure_before_any_write_is_retried_and_closes_the_trade_once(root, tmp_path, alerts):
    run, clock, *_ = trade_open_on_normal(root, tmp_path, alerts)
    run_day(run, clock, NORMAL)
    run.steps.review_exits = Flaky(run.steps.review_exits, after=False)
    run_day(run, clock, DUE)
    assert ("t1", OUTCOME_CLOSED) not in events(root, BOOK1_RULES)  # the empty case: nothing written yet
    log = run.run(DUE)
    assert log.result("exits")[BOOK1_RULES]["reviewed"] and ("t1", OUTCOME_CLOSED) in events(root, BOOK1_RULES)
    closes = [r for r in fills(root, BOOK1_RULES) if r["action"] == "close"]
    assert len(closes) == len({r["contract"] for r in fills(root, BOOK1_RULES)})  # each leg closed once


class FailingSync(LocalSync):
    """The account write of `book` raises before it writes anything (Drive unreachable)."""

    def __init__(self, root, book):
        super().__init__(root)
        self.book = book

    def write(self, book, apply, message):
        if book == self.book:
            raise TimeoutError("planted: the Drive read timed out")
        return super().write(book, apply, message)


def test_a_failed_marking_is_retried_once_and_nothing_else_repeats(root, tmp_path, alerts):
    run, clock, capture, commits = trade_open_on_normal(root, tmp_path, alerts)
    flaky = run.marking.run = Flaky(run.marking.run, after=False)
    log = run_day(run, clock, NORMAL)
    assert log.result("trade_marks")[RETRY] is True
    taken, opened = len(capture.taken), fills(root, BOOK1_RULES)
    log = run.run(NORMAL)
    assert flaky.calls == 2 and log.result("trade_marks")[BOOK1_RULES]["marked"] is True
    assert (len(capture.taken), fills(root, BOOK1_RULES)) == (taken, opened)  # no other step ran again
    assert [m for _, m in commits.made].count(f"Desk run {NORMAL} step trade_marks") == 2


def test_a_failed_step_is_retried_on_its_own_day_only(root, tmp_path, alerts):
    """A later day's run of a past day (`daily run --day`) never retries it: the next session already read its log."""
    run, clock, *_ = trade_open_on_normal(root, tmp_path, alerts)
    run_day(run, clock, NORMAL)
    flaky = run.steps.review_exits = Flaky(run.steps.review_exits, after=False)
    run_day(run, clock, DUE)
    clock.now = clock.now + timedelta(days=1)
    log = run.run(DUE)
    assert flaky.calls == 1 and log.result("exits")[RETRY] is True
    assert ("t1", OUTCOME_CLOSED) not in events(root, BOOK1_RULES)


def test_a_failed_commit_after_a_trade_was_written_still_stops_the_run(root, tmp_path, alerts):
    """Decision 44 unchanged: the fills' own count never turns a failed commit into one failed step."""
    run, clock, *_ = trade_open_on_normal(root, tmp_path, alerts, (BOOK1_RULES, BOOK2_HYBRID))
    run.steps.sync = CommitFailing(root, BOOK2_HYBRID)
    with pytest.raises(RunStopped, match="run STOPPED at step fills"):
        run_day(run, clock, NORMAL)
    assert fills(root, BOOK1_RULES) and not [t for t in alerts.sent if "step fills FAILED" in t]


class CommitFailing(FailingSync):
    def write(self, book, apply, message):
        if book == self.book:
            raise CommitFailed("planted: the push was rejected every time")
        return LocalSync.write(self, book, apply, message)
