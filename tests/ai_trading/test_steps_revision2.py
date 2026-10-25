"""Story F1t revision 2: decisions stop on BG1's level alone while G11's forecasters stop last (criterion 12); the two
steps' reasons are registered codes, so the public run log holds no book's text (criterion 17); a rehearsal never
fires a routine (criterion 18)."""

from types import SimpleNamespace

import pytest

from fno.ai.budget_stop import MeterBudgetStop
from fno.ai_trading.budget import LevelBudgetStop
from fno.ai_trading.steps import AiCollectStep, AiFireStep, ObserverHandle
from fno.budget.constants import BUDGET_STOP
from fno.constants import STEP_NOT_LIVE, STEP_OK, STEP_REFUSED
from tests.ai.fakes import Clock

from .builders import DAY, at
from .test_timing_and_steps import TIMING, Collector, Firer, Processes, Waiter

BOTH = ("book2_hybrid", "book3_ai")


def meter(level, book_minutes):
    reading = SimpleNamespace(cap=SimpleNamespace(level=level, cap_minutes=100.0),
                              usage_rows=[{"book": "book2_hybrid", "minutes": str(book_minutes)}])  # fmt: skip
    return lambda month, today: reading


@pytest.mark.parametrize(("level", "minutes", "decisions_stop", "forecasts_stop"), [
    (BUDGET_STOP, 10, True, False),  # level stop, the books far below the cap: decisions stop, forecasters fire
    (BUDGET_STOP, 100, True, True),  # the books alone at the cap: both stop
    ("alert", 100, False, False),  # alert only: both fire
])  # fmt: skip
def test_decisions_stop_on_the_level_alone_and_the_forecasters_last(level, minutes, decisions_stop, forecasts_stop):
    assert bool(LevelBudgetStop(meter(level, minutes)).check(DAY).stop) is decisions_stop
    assert bool(MeterBudgetStop(meter(level, minutes)).check(DAY).stop) is forecasts_stop


def test_an_unreadable_meter_fires_with_a_note_and_the_step_says_so(tmp_path):
    def broken(month, today):
        raise OSError("ledger missing")

    check = LevelBudgetStop(broken).check(DAY)
    assert check.stop == "" and "fail open, cost only" in check.note
    fired = {"book2_hybrid": {"state": "fired"}}
    done = AiFireStep(tmp_path, Firer(fired, note=check.note), TIMING, lambda day: ("book2_hybrid",), Processes(),
                      ObserverHandle()).run(DAY)  # fmt: skip
    assert done.result["status"] == STEP_REFUSED and "ledger missing" in done.result["reason"]
    assert AiFireStep(tmp_path, Firer(fired), TIMING, lambda day: ("book2_hybrid",), Processes(),
                      ObserverHandle()).run(DAY).result["status"] == STEP_OK  # fmt: skip


def test_every_reason_of_the_two_steps_is_a_registered_code_never_the_book_s_text(tmp_path):
    from fno.daily.public_log import PublicResult, ReasonRegistry
    from fno.daily.reason_codes import COMMON, STEP_TEMPLATES

    registry = PublicResult(ReasonRegistry(COMMON, STEP_TEMPLATES))
    fire = AiFireStep(tmp_path, Firer({"book2_hybrid": {"state": "not_fired", "reason": "cash 3,40,500 short"}}),
                      TIMING, lambda day: ("book2_hybrid",), Processes(), ObserverHandle()).run(DAY)  # fmt: skip
    shown = registry.public("ai_fire", fire.result)
    assert shown == {"status": STEP_REFUSED, "reason": "ai:NOT_FIRED", "n": 1}
    clock = Clock(at(15, 11, 2))
    collect = AiCollectStep(tmp_path, Collector({"book2_hybrid": "late"}), TIMING, lambda day: ("book2_hybrid",),
                            Waiter(clock), clock, ObserverHandle()).run(DAY)  # fmt: skip
    assert registry.public("ai_collect", collect.result)["reason"] == "ai:NOT_PROMOTED"
    assert (
        registry.public("ai_collect", {"status": STEP_OK, "reason": "every live AI book done"})["reason"] == "ai:DONE"
    )


def test_a_rehearsal_neither_fires_nor_starts_the_observer_nor_collects(tmp_path):
    firer, processes, clock = Firer({}), Processes(), Clock(at(15, 1))
    fire = AiFireStep(tmp_path, firer, TIMING, lambda day: BOTH, processes, ObserverHandle(), lambda: True).run(DAY)
    collector = Collector({})
    collect = AiCollectStep(tmp_path, collector, TIMING, lambda day: BOTH, Waiter(clock), clock, ObserverHandle(),
                            lambda: True).run(DAY)  # fmt: skip
    assert firer.calls == 0 and processes.started == [] and collector.called_at is None
    for done in (fire, collect):
        assert done.result["status"] == STEP_REFUSED and done.result["reason"].startswith("rehearsal: AI decision")
    quiet = AiFireStep(tmp_path, firer, TIMING, lambda day: (), processes, ObserverHandle(), lambda: True).run(DAY)
    assert quiet.result["status"] == STEP_NOT_LIVE  # no book live: as in a real run


def test_the_strategy_label_of_a_promoted_book_stays_in_the_public_run_log(tmp_path):
    from fno.ai_trading.collect import Collected
    from fno.daily.public_log import PublicResult, ReasonRegistry
    from fno.daily.reason_codes import COMMON, STEP_TEMPLATES

    class Labelled(Collector):
        def collect(self, day, books, deadlines, late_at=None):
            return Collected({"book2_hybrid": {"status": "promoted", "reason": "r", "strategy_label":
                                               "strategy not yet passed"}}, ())  # fmt: skip

    clock = Clock(at(15, 11, 2))
    done = AiCollectStep(tmp_path, Labelled({}), TIMING, lambda day: ("book2_hybrid",), Waiter(clock), clock,
                         ObserverHandle()).run(DAY)  # fmt: skip
    shown = PublicResult(ReasonRegistry(COMMON, STEP_TEMPLATES)).public("ai_collect", done.inputs)
    assert shown["strategy_labels"] == {"book2_hybrid": "strategy_not_yet_passed"}
