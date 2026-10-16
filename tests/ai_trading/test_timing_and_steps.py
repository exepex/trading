"""Story F1t criteria 1, 3e and 11: the decision timetable is checked at load; with no live book both steps record
`not_live` and call nothing; `ai_fire` starts the remote observer once; `ai_collect` waits for its last reading,
then reports `ok` only when every live book was promoted, else `refused` naming each book."""

from datetime import timedelta

import pytest

from fno.ai.observed_receipts import Observation, ObservationFile
from fno.ai_trading.paths import observations_path
from fno.ai_trading.steps import AiCollectStep, AiFireStep
from fno.ai_trading.timing import DecisionTimingError, decision_timing_from_config
from fno.config import load_app_config
from fno.constants import STEP_NOT_LIVE, STEP_OK, STEP_REFUSED
from fno.desk.timetable import timetable_from_config
from tests.ai.fakes import Clock

from .builders import DAY, at

CFG = load_app_config()
TIMING = decision_timing_from_config(CFG, timetable_from_config(CFG))


def timing(**changes):
    cfg = {"ai_books": {"decision_timing": CFG["ai_books"]["decision_timing"] | changes}, "desk": CFG["desk"]}
    return decision_timing_from_config(cfg, timetable_from_config(cfg))


def test_the_configured_timetable_is_in_order_and_before_e3_s_deadline():
    assert TIMING.deadlines(DAY).receipt == at(15, 10) and TIMING.deadlines(DAY).reveal == at(15, 11)
    assert TIMING.fire_timing(DAY).latest_fire == at(15, 7)


@pytest.mark.parametrize("changes, why", [
    ({"latest_fire": "15:10:00"}, "latest_fire must be before receipt_deadline"),
    ({"reveal_from": "15:10:00"}, "receipt_deadline must be before reveal_from"),
    ({"reveal_deadline": "15:12:00"}, "before desk.timetable.decision_deadline"),
    ({"reveal_deadline": "noon"}, "reveal_deadline is not a time"),
])  # fmt: skip
def test_a_timetable_out_of_order_is_refused_naming_the_key(changes, why):
    with pytest.raises(DecisionTimingError, match=why):
        timing(**changes)


def test_a_missing_key_is_refused():
    cfg = {"ai_books": {"decision_timing": {"latest_fire": "15:07"}}, "desk": CFG["desk"]}
    with pytest.raises(DecisionTimingError, match="receipt_deadline is missing"):
        decision_timing_from_config(cfg, timetable_from_config(cfg))


class Untouchable:
    def __getattr__(self, name):
        raise AssertionError(f"called {name} with no live book")


class Processes:
    def __init__(self):
        self.started = []

    def start(self, arguments):
        self.started.append(arguments)
        return object()


class Firer:
    def __init__(self, log):
        self.log, self.calls = log, 0

    def fire(self, day, books, fire_timing):
        self.calls += 1
        return {book: self.log[book] for book in books}


def test_with_no_live_book_both_steps_are_not_live_and_call_nothing(tmp_path):
    fire = AiFireStep(tmp_path, Untouchable(), TIMING, lambda day: (), Untouchable())
    collect = AiCollectStep(tmp_path, Untouchable(), TIMING, lambda day: (), Untouchable(), Untouchable())
    for step in (fire, collect):
        done = step.run(DAY)
        assert done.result["status"] == STEP_NOT_LIVE and done.paths == ()


def test_ai_fire_starts_the_observer_once_and_reports_each_book_not_fired(tmp_path):
    processes = Processes()
    log = {"book2_hybrid": {"state": "fired"}, "book3_ai": {"state": "not_fired", "reason": "budget stop"}}
    step = AiFireStep(tmp_path, Firer(log), TIMING, lambda day: ("book2_hybrid", "book3_ai"), processes)
    done = step.run(DAY)
    (arguments,) = processes.started
    assert arguments[:3] == ("ai", "observe-remote", "--out") and arguments[-3:] == (
        at(15, 10).isoformat(),
        "--deadline",
        at(15, 11).isoformat(),
    )
    assert done.result == {
        "status": STEP_REFUSED,
        "reason": "book3_ai not fired: budget stop; no trade today for these",
    }
    ObservationFile(tmp_path / observations_path(DAY)).append(
        Observation(at(15, 10), at(15, 10), at(15, 10, 1), "c1"))  # fmt: skip
    step.run(DAY)
    assert len(processes.started) == 1  # a rerun with readings starts none (a late reading proves nothing)
    assert AiFireStep(tmp_path, Firer({"book2_hybrid": {"state": "fired"}}), TIMING, lambda day: ("book2_hybrid",),
                      processes).run(DAY).result["status"] == STEP_OK  # fmt: skip


class Collector:
    def __init__(self, statuses):
        self.statuses, self.called_at = statuses, None

    def collect(self, day, books, deadlines):
        from fno.ai_trading.collect import Collected

        return Collected({b: {"status": s, "reason": "why"} for b, s in self.statuses.items()}, ())


class Waiter:
    def __init__(self, clock, then=None):
        self.clock, self.then = clock, then

    def until(self, moment):
        self.clock.now = moment
        if self.then:
            self.then(self.clock.now)


@pytest.mark.parametrize(
    "statuses, status",
    [({"book2_hybrid": "promoted"}, STEP_OK), ({"book2_hybrid": "promoted", "book3_ai": "late"}, STEP_REFUSED)],
)
def test_ai_collect_waits_for_the_last_reading_then_reports(tmp_path, statuses, status):
    clock, readings = Clock(at(15, 10, 30)), ObservationFile(tmp_path / observations_path(DAY))

    def reading_arrives(now):
        if now >= at(15, 11, 1) and not readings.read():
            readings.append(Observation(at(15, 11), at(15, 11), at(15, 11, 1), "c2"))

    waiter = Waiter(clock, reading_arrives)
    step = AiCollectStep(tmp_path, Collector(statuses), TIMING, lambda day: tuple(statuses), waiter, clock)
    done = step.run(DAY)
    assert clock.now == at(15, 11, 1) and done.result["status"] == status
    if status == STEP_REFUSED:
        assert done.result["reason"] == "book3_ai late: why; no trade today for these"


def test_ai_collect_gives_up_waiting_when_the_reading_can_no_longer_be_valid(tmp_path):
    clock = Clock(at(15, 10, 30))
    step = AiCollectStep(tmp_path, Collector({"book2_hybrid": "late"}), TIMING, lambda day: ("book2_hybrid",),
                         Waiter(clock), clock)  # fmt: skip
    step.run(DAY)
    assert clock.now == at(15, 11) + timedelta(seconds=50)  # 30 s grace + the 20 s bound of one remote read
