"""Story F1t, the code round's own reviews (25 Oct): each found problem with the test that pins its fix."""

import json
from datetime import time

import pytest

from fno.ai_trading.budget import LevelBudgetStop
from fno.ai_trading.outcome import PROMOTED, REFUSED
from fno.ai_trading.records import OutcomeRecords
from fno.ai_trading.timing import DecisionTimingError
from fno.ai_trading.wiring import ai_day_steps
from fno.constants import STEP_NOT_LIVE
from fno.playbook.decision_store import DecisionStore

from .builders import DAY, at, draft
from .day import BOOKS, DEADLINES, Day
from .test_timing_and_steps import CFG, timing


def sealed_day(tmp_path):
    day = Day(tmp_path)
    day.fire()
    for book in BOOKS:
        day.seal(book, draft())
    day.observe(DEADLINES.receipt)
    for book in BOOKS:
        day.reveal(book)
    day.observe(DEADLINES.reveal)
    return day


def test_a_collection_reaching_a_book_at_e3_s_deadline_records_late_and_promotes_nothing(tmp_path):
    day = sealed_day(tmp_path)
    day.clock.now = at(15, 12)  # exactly the deadline: a run committed now is late by E3's rule
    outcomes = day.collect(late_at=at(15, 12)).outcomes
    assert {b: o["status"] for b, o in outcomes.items()} == dict.fromkeys(BOOKS, "late")
    assert all(not d.calls for d in day.deciders.values())


def test_more_than_the_reserve_before_the_deadline_still_promotes(tmp_path):
    day = sealed_day(tmp_path)
    day.clock.now = at(15, 11, 49)  # 11 s left: 1 s for the decider after the 10 s reserve
    assert day.collect(late_at=at(15, 12)).outcomes["book2_hybrid"]["status"] == PROMOTED


def test_within_the_reserve_before_the_deadline_is_late_and_no_decider_runs(tmp_path):
    """Judge 651 should-fix 1: the run check, snapshots and record need the last 10 s before E3 collects."""
    day = sealed_day(tmp_path)
    day.clock.now = at(15, 11, 50)
    outcomes = day.collect(late_at=at(15, 12)).outcomes
    assert {b: o["status"] for b, o in outcomes.items()} == dict.fromkeys(BOOKS, "late")
    assert "did not finish within 0.0 s" in outcomes["book2_hybrid"]["reason"]
    assert all(not d.calls for d in day.deciders.values())


def test_a_run_finished_at_or_after_the_deadline_is_put_back_and_late(tmp_path):
    """A decider the alarm could not stop (no main thread) is still never collected: the check after it undoes it."""
    day = sealed_day(tmp_path)
    day.clock.now = at(15, 11, 0)
    decider = day.deciders["book2_hybrid"]
    original = decider.decide

    def slow(accepted):
        decided = original(accepted)
        day.clock.now = at(15, 12, 5)
        return decided

    decider.decide = slow
    outcomes = day.collect(books=("book2_hybrid",), late_at=at(15, 12)).outcomes
    assert outcomes["book2_hybrid"]["status"] == "late" and "finished at 15:12:05" in outcomes["book2_hybrid"]["reason"]
    assert outcomes["book2_hybrid"]["run_id"] == "" and DecisionStore(day.root, "book2_hybrid").runs(DAY) == []


def test_a_record_that_cannot_be_written_after_promotion_puts_the_run_back(tmp_path, monkeypatch):
    day = sealed_day(tmp_path)
    real = OutcomeRecords.write

    def fails_once_for_book2(self, d, outcome, *args, **kwargs):
        if outcome.book == "book2_hybrid" and outcome.status == PROMOTED:
            raise OSError("disk full")
        return real(self, d, outcome, *args, **kwargs)

    monkeypatch.setattr(OutcomeRecords, "write", fails_once_for_book2)
    outcomes = day.collect().outcomes
    assert outcomes["book2_hybrid"]["status"] == REFUSED and outcomes["book3_ai"]["status"] == PROMOTED
    assert DecisionStore(day.root, "book2_hybrid").every_run() == []  # never a run left without its record


def test_an_early_reveal_by_a_book_already_recorded_still_exposes_the_other(tmp_path):
    day = Day(tmp_path)
    day.fire()
    day.seal("book2_hybrid", draft())
    day.seal("book3_ai", draft())
    with day._own_folder("book3_ai"):
        day.routines["book3_ai"].session().publisher.wait_until = lambda moment: None  # reveals at once: early
        day.routines["book3_ai"].session().reveal()
    day.observe(DEADLINES.receipt)
    day.reveal("book2_hybrid")
    day.observe(DEADLINES.reveal)
    day.collect(books=("book3_ai",))  # book 3's own record first (an interrupted earlier collection)
    assert day.collect().outcomes["book2_hybrid"]["status"] == "exposed"


def test_a_timetable_leaving_the_collection_no_time_before_e3_s_deadline_is_refused():
    with pytest.raises(DecisionTimingError, match="the collection needs time"):
        timing(reveal_deadline="15:11:20")  # +30 s grace +20 s reading = 15:12:10, after E3's 15:12
    assert timing().promotion_deadline == time(15, 12)


def test_a_bad_timetable_is_not_read_while_no_ai_book_is_live(tmp_path):
    cfg = json.loads(json.dumps(CFG, default=str)) | {"ai_books": {"decision_timing": {"latest_fire": "nonsense"}}}
    books, steps, parts = ai_day_steps(cfg, tmp_path, DAY, None, None, None, None, None, None)
    assert books == () and parts == {} and all(s.run(DAY).result["status"] == STEP_NOT_LIVE for s in steps.values())


def test_a_null_budget_block_fails_open_on_cost_only():
    def meter(month, today):
        raise AttributeError("'NoneType' object has no attribute 'get'")

    check = LevelBudgetStop(meter).check(DAY)
    assert check.stop == "" and "AttributeError" in check.note


@pytest.mark.parametrize("rehearsing", [True, False])
def test_the_wiring_builds_no_routine_trigger_in_a_rehearsal_and_its_steps_refuse(tmp_path, monkeypatch, rehearsing):
    """Judge 651 should-fix 2, on the real wiring and the real mode: in a rehearsal no `RoutineTrigger` is built (the
    factory is a spy) and both steps refuse; in a real run both triggers are built."""
    from datetime import datetime

    from fno.ai_trading import wiring
    from fno.models import IST
    from fno.rehearsal.mode import Rehearsal, in_this_process

    built = []
    monkeypatch.setattr(wiring, "build_decision_trigger", lambda book, env: built.append(book))
    live = lambda day: ("book2_hybrid",)  # noqa: E731
    clock = lambda: datetime.combine(DAY, time(15, 1), IST)  # noqa: E731
    arguments = (CFG, tmp_path, live, {}, None, None, None, None, clock)
    if rehearsing:
        with in_this_process(Rehearsal.new(DAY, tmp_path / "home", tmp_path)):
            steps = wiring.build_ai_steps(*arguments)
            results = [step.run(DAY).result for step in steps.values()]
        assert built == [] and all(r["reason"].startswith("rehearsal: AI decision") for r in results)
    else:
        wiring.build_ai_steps(*arguments)
        assert sorted(built) == ["book2_hybrid", "book3_ai"]
