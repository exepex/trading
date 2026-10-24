"""DRY2 R2 (24 Oct): an unexpected error in one desk step fails that step only. It is logged with its type and one
line and alerted, the run goes on, and a step that reads the failed step's result is refused, never run on a missing
input. A failed commit or git read still stops the run (decision 44, unchanged)."""

from datetime import date

from fno.constants import BOOK1_RULES, STEP_FAILED, STEP_REFUSED
from fno.desk.daily_run import NEEDS_FAILED, NOT_REVIEWED

from .fakes import C4, Decisions, Rules, daily_run
from .test_daily_run import NORMAL, decided, run_day

NEXT = date(2026, 10, 15)


class Planted:
    def __init__(self, error):
        self.error = error

    def capture(self, day):
        raise self.error


def planted_run(root, tmp_path, alerts):
    decisions = Decisions()
    decisions.add(*decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    run, clock, *_ = daily_run(root, tmp_path, alerts, (BOOK1_RULES,), decisions, C4(), Rules())
    return run, clock


def test_a_planted_error_in_the_snapshot_fails_that_step_refuses_the_fills_and_the_run_goes_on(root, tmp_path, alerts):
    run, clock = planted_run(root, tmp_path, alerts)
    run.steps.capture = Planted(NotImplementedError("planted: the store cannot list a folder\nsecond line"))
    log = run_day(run, clock, NORMAL)
    assert log.result("snapshot") == {
        "status": STEP_FAILED,
        "reason": "NotImplementedError: planted: the store cannot list a folder",
    }
    assert log.result("fills") == {"status": STEP_REFUSED, "reason": NEEDS_FAILED.format(needed="snapshot")}
    assert log.done("exits") and log.done("trade_marks")  # risk-reducing exits always run; the marks too
    assert [t for t in alerts.sent if "step snapshot FAILED (NotImplementedError: planted" in t]
    assert "the run goes on" in alerts.sent[[i for i, t in enumerate(alerts.sent) if "FAILED" in t][0]]


def test_a_failed_exits_step_leaves_every_book_unreviewed_for_the_next_session(root, tmp_path, alerts):
    run, clock = planted_run(root, tmp_path, alerts)

    def broken(day):
        raise KeyError("planted")

    run.steps.review_exits = broken
    log = run_day(run, clock, NORMAL)
    assert log.result("exits")["status"] == STEP_FAILED
    assert run._unreviewed(NEXT) == {BOOK1_RULES: NOT_REVIEWED.format(day=NORMAL, why="KeyError: 'planted'")}
