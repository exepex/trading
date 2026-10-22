"""Story O1-desk-freeze: one switch freezes the paper desk's daily steps. A frozen step keeps its time (the 3 pm parts
are serviced in those waits) and records `frozen`; every other step runs as ever; an open position keeps what it
needs; the session after a frozen one blocks nothing."""

import json

import pytest

from fno.books.account import PaperAccount
from fno.constants import (
    BOOK1_RULES,
    DAILY_RUN_STEPS,
    DESK_FROZEN_STEPS,
    DESK_RUN_STEPS,
    OPEN_POSITION_STEPS,
    OUTCOME_OPENED,
    STEP_FROZEN,
    STEP_OK,
)
from fno.daily.desk_freeze import DeskFreeze, desk_frozen, open_trades
from fno.daily.runner import DAY_DONE
from fno.daily.wiring import public_recorder
from fno.desk.run_log import RunLog
from fno.desk.trade_marking import marked_accounts
from tests.desk.builders import at
from tests.timetable.fakes import C4, Decisions, Rules, daily_run
from tests.timetable.test_daily_run import NORMAL, SLOW, decided

from .test_day_run import day  # noqa: F401 - the fixture: one day of the run over E3's real DailyRun

O1_DESK = ("book1", "owner_timing_fills", "reviews", "card")
FROZEN_ALL = DeskFreeze(True, lambda: 0)


def test_the_frozen_set_is_the_desk_and_never_a_quote_forecast_score_candle_or_close_step():
    """Acceptance 7: a planted non-desk step (`quotes_done`, say) in the frozen set fails here."""
    assert set(DESK_FROZEN_STEPS) == {*DESK_RUN_STEPS, *O1_DESK} and set(DESK_FROZEN_STEPS) <= set(DAILY_RUN_STEPS)
    assert set(OPEN_POSITION_STEPS) < set(DESK_FROZEN_STEPS)
    assert not {"quotes", "quotes_done", "margin_check", "weather", "forecasts_v4", "candles"} & set(DESK_FROZEN_STEPS)


SWITCHES = [({}, False), ({"desk": {}}, False), ({"desk": None}, False), ({"desk": {"frozen": False}}, False),
            ({"desk": {"frozen": True}}, True)]  # fmt: skip


@pytest.mark.parametrize(("cfg", "frozen"), SWITCHES)
def test_the_switch_is_absent_false_or_true(cfg, frozen):
    assert desk_frozen(cfg) is frozen


@pytest.mark.parametrize("value", ["yes", 1, "true", None])
def test_anything_but_a_boolean_switch_is_refused(value):
    with pytest.raises(ValueError, match="desk.frozen must be true or false"):
        desk_frozen({"desk": {"frozen": value}})


def test_the_switch_off_freezes_nothing_and_never_reads_the_accounts():
    def unread():
        raise AssertionError("the accounts were read")

    assert DeskFreeze(False, unread)(NORMAL) == frozenset()


def test_an_open_position_keeps_what_it_needs_and_nothing_new_opens():
    assert DeskFreeze(True, lambda: 2)(NORMAL) == frozenset(DESK_FROZEN_STEPS) - set(OPEN_POSITION_STEPS)
    assert {"versions", "decisions", "fills", "book1", "owner_timing_fills", "card"} <= DeskFreeze(True, lambda: 2)(
        NORMAL
    )


def test_a_frozen_session_records_each_desk_step_frozen_keeps_its_times_and_runs_everything_else(day, alerts):  # noqa: F811
    runner, run, _, parts, commits, calls = day()
    run.frozen, run.recorder = FROZEN_ALL, public_recorder(run.steps.root)
    assert runner.run(NORMAL) == (0, DAY_DONE) and alerts.sent == []
    steps = run.run(NORMAL).steps
    assert tuple(steps) == DAILY_RUN_STEPS
    assert {name: steps[name]["result"] for name in DESK_FROZEN_STEPS} == dict.fromkeys(
        DESK_FROZEN_STEPS, {"status": STEP_FROZEN, "reason": "desk:FROZEN"})  # fmt: skip
    assert not set(O1_DESK) & set(calls)  # no `desk book1`, no reviews, no card
    assert steps["decisions"]["started_at"] == at(15, 12, day=NORMAL).isoformat()  # the timetable is unchanged
    assert steps["snapshot"]["started_at"] == at(15, 15, day=NORMAL).isoformat()
    assert steps["quotes_done"]["started_at"] >= steps["snapshot"]["started_at"]
    assert steps["quotes_done"]["result"]["status"] == STEP_OK
    assert [message.split()[-1] for _, message, _ in commits] == ["nifty", "nse", "indices"]
    assert PaperAccount(run.steps.root, BOOK1_RULES).fills() == []  # nothing filled though t1 was decided


def e3_run(root, tmp_path, alerts):
    decisions = Decisions()
    for when, trade_id in ((NORMAL, "t1"), (SLOW, "t2")):
        decisions.add(*decided(BOOK1_RULES, trade_id, when), when)
    run, clock, *_ = daily_run(root, tmp_path, alerts, (BOOK1_RULES,), decisions, C4(), Rules())
    return run, clock


def test_with_an_open_trade_its_exits_marks_and_loss_rules_run_at_the_snapshot_and_nothing_new_opens(
    root, tmp_path, alerts
):
    """Acceptance 6: the frozen set is read from the accounts as downloaded (open t1 from the session before)."""
    run, clock = e3_run(root, tmp_path, alerts)
    clock.now = at(14, 50, day=NORMAL)
    run.run(NORMAL)  # the desk not frozen: t1 opens
    run.frozen = DeskFreeze(True, lambda: open_trades(root, marked_accounts(root, (BOOK1_RULES,))))
    clock.now = at(14, 50, day=SLOW)
    log = run.run(SLOW)
    frozen = {name for name, step in log.steps.items() if step["result"].get("status") == STEP_FROZEN}
    assert frozen == {"versions", "decisions", "fills"} and log.result("snapshot")["valid"] is True
    assert log.result("exits")[BOOK1_RULES] == {"reviewed": True, "results": [
        {"trade_id": "t1", "outcome": "held", "reason": "no exit rule reached"}]}  # fmt: skip
    assert log.result("trade_marks")[BOOK1_RULES]["trades"] == [{"trade_id": "t1", "status": "valued"}]
    assert alerts.sent == [] and {f.trade_id for f in PaperAccount(root, BOOK1_RULES).fills()} == {"t1"}


def test_the_session_after_a_frozen_one_runs_the_whole_desk_and_blocks_nothing(root, tmp_path, alerts):
    """Acceptance 4: the frozen session's exits were never reviewed, and that is not a reason to block."""
    run, clock = e3_run(root, tmp_path, alerts)
    run.frozen = FROZEN_ALL
    clock.now = at(14, 50, day=NORMAL)
    run.run(NORMAL)
    run.frozen = DeskFreeze(False, lambda: 0)  # the owner's one line: desk.frozen: false
    clock.now = at(14, 50, day=SLOW)
    log = run.run(SLOW)
    assert log.result("fills")["t2"]["outcome"] == OUTCOME_OPENED and alerts.sent == []
    assert run._unreviewed(SLOW) == {} and run._unscored(SLOW) == {}


def test_the_frozen_record_holds_status_and_code_only(day):  # noqa: F811
    runner, run, *_ = day()
    run.frozen, run.recorder = FROZEN_ALL, public_recorder(run.steps.root)
    runner.run(NORMAL)
    committed = json.loads(RunLog.open(run.steps.root, NORMAL).path.read_text(encoding="utf-8"))
    assert (
        committed["steps"]["card"]["inputs"] == {} and committed["steps"]["fills"]["result"]["reason"] == "desk:FROZEN"
    )
