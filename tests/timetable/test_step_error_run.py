"""DRY2 R2 (24 Oct): an unexpected error in one desk step fails that step only. It is logged with its type and one
line and alerted, the run goes on, and a step that reads the failed step's result is refused, never run on a missing
input. A failed commit or git read still stops the run (decision 44, unchanged)."""

from datetime import date, datetime, time

from fno.constants import BOOK1_RULES, STEP_FAILED, STEP_REFUSED
from fno.desk.daily_run import NEEDS_FAILED, NOT_REVIEWED

from .fakes import C4, Decisions, Rules, daily_run
from .test_daily_run import NORMAL, decided, fills, run_day

NEXT = date(2026, 10, 15)


def rerun(run, clock):
    """A same-day rerun starts later than the first run (CLAUDE.md: rerun `fno daily run` after a problem)."""
    from fno.models import IST

    clock.now = datetime.combine(NORMAL, time(15, 16), IST)
    return run.run(NORMAL)


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
        "retry": True,
    }
    assert log.result("fills") == {"status": STEP_REFUSED, "reason": NEEDS_FAILED.format(needed="snapshot"),
                                   "retry": True}  # fmt: skip
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


def test_a_same_day_rerun_retries_a_step_failed_by_an_unexpected_error_and_repeats_no_finished_step(
    root, tmp_path, alerts
):
    """Judge 569 SF1 and the orchestrator's ruling: a retry-safe step that failed is run again by the rerun."""
    run, clock = planted_run(root, tmp_path, alerts)
    capture = run.steps.capture
    run.steps.capture = Planted(NotImplementedError("planted"))
    first = run_day(run, clock, NORMAL)
    assert (
        first.result("snapshot")["retry"] is True
        and "a same-day rerun" in alerts.sent[-1]
        or any("a same-day rerun (`fno daily run`) retries it" in t for t in alerts.sent)
    )
    versions = first.steps["versions"]["finished_at"]
    run.steps.capture = capture
    again = rerun(run, clock)
    assert again.result("snapshot").get("valid") is True and again.steps["versions"]["finished_at"] == versions
    assert again.result("fills")["t1"]["outcome"] == "opened"  # the refused fills ran once their input was there


def test_a_retried_fills_step_never_doubles_the_trades_written_before_its_error(root, tmp_path, alerts):
    """Judge 570: fills go trade by trade; an error after one trade says so, and the retry enters only the rest."""
    decisions = Decisions()
    decisions.add(*decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    decision, orders = decided(BOOK1_RULES, "t2", NORMAL)
    decisions.add(decision, orders + decided(BOOK1_RULES, "t1", NORMAL)[1], NORMAL)
    run, clock, *_ = daily_run(root, tmp_path, alerts, (BOOK1_RULES,), decisions, C4(), Rules())
    real, calls = run.steps._fill_one, []

    def second_fails(*args):
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("planted after one trade")
        return real(*args)

    run.steps._fill_one = second_fails
    first = run_day(run, clock, NORMAL)
    assert first.result("fills") == {"status": STEP_FAILED, "reason": "RuntimeError: planted after one trade",
                                     "retry": True}  # fmt: skip
    assert any("1 trade(s) written before the error stay in the account" in t for t in alerts.sent)
    written = fills(root, BOOK1_RULES)
    run.steps._fill_one = real
    rerun(run, clock)
    after = fills(root, BOOK1_RULES)
    ids = [row["fill_id"] for row in after]
    assert len(ids) == len(set(ids)) and len(after) > len(written)  # no row twice; the rest entered


def test_failed_decisions_refuse_the_fills_naming_them_and_fill_nothing(root, tmp_path, alerts):
    """Judge 569 SF2 and judge 570: the decisions half of `NEEDS`."""
    run, clock = planted_run(root, tmp_path, alerts)

    def broken(day):
        raise KeyError("planted")

    run.steps.collect_decisions = broken
    log = run_day(run, clock, NORMAL)
    assert log.result("fills") == {"status": STEP_REFUSED, "reason": NEEDS_FAILED.format(needed="decisions"),
                                   "retry": True}  # fmt: skip
    assert fills(root, BOOK1_RULES) == []


def test_a_step_not_safe_to_retry_is_final_and_says_so(root, tmp_path, alerts):
    from fno.desk.daily_run import NOT_RETRIED

    run, clock = planted_run(root, tmp_path, alerts)

    class Card:
        runs = 0

        def run(self, day):
            Card.runs += 1
            raise RuntimeError("planted after a post")

    run.day_steps["card"] = Card()
    first = run_day(run, clock, NORMAL)
    assert first.result("card")["retry"] is False and any(f"final today: {NOT_RETRIED}" in t for t in alerts.sent)
    run_day(run, clock, NORMAL)
    assert Card.runs == 1
