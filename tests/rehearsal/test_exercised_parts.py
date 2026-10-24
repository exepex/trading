"""REH1j, J4: a quote part not live on the replayed day never decides `quotes_done`; its result is kept apart."""

from datetime import date

from fno.constants import STEP_FAILED, STEP_OK
from fno.daily.quote_parts import QuotePart
from fno.daily.quote_steps import parts_result
from fno.desk.daily_ports import DayStep
from fno.desk.daily_steps import StepOutcome
from fno.rehearsal.exercised_parts import EXERCISED_PARTS, ExercisedPartsApart, rehearsed_quotes_done

DAY = date(2026, 10, 23)
OK, FAILED = {"status": STEP_OK}, {"status": STEP_FAILED, "reason": "no v4 capture recorded"}
PARTS = (QuotePart("nifty", ("quotes", "record"), ()), QuotePart("v4", ("quotes", "record", "--window", "v4"), (),
                                                                  live_key="v4_pack"))  # fmt: skip


class Finished(DayStep):
    def __init__(self, results: dict | None):
        self.results = results

    def run(self, day):
        if self.results is None:
            return StepOutcome({}, {"status": STEP_FAILED, "reason": "OSError: raised"})
        return StepOutcome({}, parts_result(self.results), ("a",))


def test_a_failed_not_live_part_beside_ok_live_parts_leaves_the_step_ok():
    step = rehearsed_quotes_done(Finished({"nifty": OK, "v4": FAILED}), PARTS, {"v4_pack": "note"})
    done = step.run(DAY)
    assert done.result == {"status": STEP_OK, "reason": "every part ok", "parts": {"nifty": OK},
                           EXERCISED_PARTS: {"v4": FAILED}}  # fmt: skip
    assert done.paths == ("a",)


def test_a_failed_live_part_still_fails_the_step():
    done = ExercisedPartsApart(Finished({"nifty": FAILED, "v4": OK}), {"v4"}).run(DAY)
    assert done.result["status"] == STEP_FAILED and done.result["reason"] == "not ok: nifty"


def test_with_every_part_live_the_step_is_as_today():
    step = Finished({"nifty": OK, "v4": FAILED})
    assert rehearsed_quotes_done(step, PARTS, {}) is step
    assert step.run(DAY).result["status"] == STEP_FAILED


def test_a_step_that_never_reached_its_parts_keeps_its_own_result():
    done = ExercisedPartsApart(Finished(None), {"v4"}).run(DAY)
    assert done.result == {"status": STEP_FAILED, "reason": "OSError: raised"}
