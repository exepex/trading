"""DRY2 SF1 and SF2: a desk step not safe to repeat stays failed for the day, its alert says a rerun will not retry it,
and the fills it feeds stay refused (a refused step is never retried). Judge 569 SF2 and judge 570 minor 1: with the
decisions step failed, the fills step is refused naming the decisions, and no fill is made, before or after a rerun."""

import pytest

from fno.constants import BOOK1_RULES, STEP_FAILED, STEP_REFUSED
from fno.desk.daily_run import NEEDS_FAILED, NOT_RETRIED, RERUN_FINAL, DailyRun
from fno.desk.run_log import RETRY, RunLog
from tests.desk.builders import at

from .fakes import C4, Decisions, Rules, daily_run
from .test_daily_run import NORMAL, decided, fills, run_day

PLANTED = "KeyError: 'planted'"
AT = at(15, 15, day=NORMAL)


class Raising:
    def __init__(self):
        self.calls = 0

    def __call__(self, day):
        self.calls += 1
        raise KeyError("planted")


def one_book_run(root, tmp_path, alerts):
    decisions = Decisions()
    decisions.add(*decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    return daily_run(root, tmp_path, alerts, (BOOK1_RULES,), decisions, C4(), Rules())


@pytest.mark.parametrize(("name", "action"), [("decisions", "collect_decisions"), ("snapshot", "take_snapshot")])
def test_a_step_not_safe_to_repeat_stays_failed_and_its_fills_stay_refused(root, tmp_path, alerts, name, action):
    run, clock, capture, _ = one_book_run(root, tmp_path, alerts)
    raising = Raising()
    setattr(run.steps, action, raising)
    log = run_day(run, clock, NORMAL)
    assert log.result(name) == {"status": STEP_FAILED, "reason": PLANTED, "retry": False} and log.done(name)
    assert log.result("fills") == {"status": STEP_REFUSED, "reason": NEEDS_FAILED.format(needed=name)}
    assert not fills(root, BOOK1_RULES)
    final = RERUN_FINAL.format(why=NOT_RETRIED[name])
    assert [t for t in alerts.sent if f"step {name} FAILED ({PLANTED})" in t and t.endswith(final)]

    taken = len(capture.taken)
    log = run.run(NORMAL)  # the owner's rerun the same day: neither the failed step nor the refused fills run again
    assert raising.calls == 1 and log.result("fills")["status"] == STEP_REFUSED and not fills(root, BOOK1_RULES)
    assert len(capture.taken) == taken


@pytest.mark.parametrize(("name", "action"), [("versions", "keep_versions"), ("pack", "build_pack")])
def test_a_failed_version_keeping_or_pack_is_not_retried_after_its_readers_ran(root, tmp_path, alerts, name, action):
    run, clock, *_ = one_book_run(root, tmp_path, alerts)
    raising = Raising()
    setattr(run.steps, action, raising)
    log = run_day(run, clock, NORMAL)
    assert log.result(name) == {"status": STEP_FAILED, "reason": PLANTED, RETRY: False}
    assert [t for t in alerts.sent if t.endswith(RERUN_FINAL.format(why=NOT_RETRIED[name]))]
    run.run(NORMAL)
    assert raising.calls == 1


def test_a_needed_step_awaiting_its_retry_refuses_as_failed_not_as_missing(tmp_path):
    log = RunLog.open(tmp_path, NORMAL)
    for name, result in (("decisions", {BOOK1_RULES: {"run_id": "r1"}}),
                         ("snapshot", {"status": STEP_FAILED, "reason": PLANTED, RETRY: True})):  # fmt: skip
        log.record(name, AT, AT, {}, result)
    refused = DailyRun._refused(None, log, "fills")
    assert refused.result == {"status": STEP_REFUSED, "reason": NEEDS_FAILED.format(needed="snapshot")}
