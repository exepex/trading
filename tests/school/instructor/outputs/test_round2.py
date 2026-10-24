"""Part e's round 2 (judge 522): a corrected outcome re-attributed and re-classified even when nothing was waiting;
the day's run lists orphans; and one test for each branch the judge could break with every test green."""

from dataclasses import replace
from datetime import date

from fno.school.constants import SLOT_1500, RecordKind
from fno.school.instructor.contracts import Cause, Modifier, record_sha256
from fno.school.instructor.outputs.comparison import CountedComparison, sealed_decisions
from fno.school.instructor.outputs.controls import control_nets, controls_for
from fno.school.instructor.outputs.review import _drawdown
from fno.school.instructor.outputs.run import waiting
from fno.school.instructor.ports import InstructorKind
from tests.school.instructor.builders import SESSIONS, classification, held_trade, refilled
from tests.school.instructor.outputs.test_review import CARDS, scenario
from tests.school.instructor.outputs.test_run import instructor
from tests.school.instructor.reading import LATER, WriteRefusingDashcam, correct_later, reader

NEXT = date(2026, 11, 6)


def settled_first_run():
    """A first run whose record waits for nothing: the stored classification is rewritten as settled and compared."""
    run, record = instructor()
    first = run.for_session(SESSIONS[2], write=True).classifications[0]
    done = replace(first, not_testable=(), modifier=Modifier.HARD_ROAD)
    del run.store.files[(SESSIONS[2], InstructorKind.CAUSES)]
    run.store.write(SESSIONS[2], InstructorKind.CAUSES, (done,))
    return run, record, done


def test_a_corrected_outcome_is_re_attributed_and_re_classified_even_when_nothing_waited():
    run, record, done = settled_first_run()
    assert not waiting(done)
    dashcam = run.reader.dashcam
    fixed = correct_later(dashcam, record, day=LATER, exit_price=15.0)  # net -140 becomes -230
    later, _ = instructor(store=run.store)
    later.reader = reader(dashcam)
    result = later.for_session(NEXT, write=True)
    (attribution,) = result.attributions
    (again,) = result.classifications
    first_attribution = run.store.read(SESSIONS[2], InstructorKind.ATTRIBUTION)[0]
    assert attribution.net == fixed.net == again.net and attribution.corrects == record_sha256(first_attribution)
    assert again.corrects == record_sha256(done) and again.outcome_sha256 == record_sha256(fixed)


def test_an_unchanged_record_is_never_written_again():
    run, _ = instructor()
    run.for_session(SESSIONS[2], write=True)
    assert run.for_session(LATER, write=True).classifications == ()  # waiting, re-checked, unchanged: nothing new


def test_the_modifier_alone_makes_a_record_wait():
    assert waiting(classification(modifier=Modifier.NOT_TESTABLE))
    assert waiting(classification(not_testable=(Cause.EXIT_WHIPSAW,)))
    assert not waiting(classification(modifier=Modifier.HARD_ROAD))


def test_the_days_run_lists_orphan_corrections():
    run, record = instructor()
    stray = refilled(record, 13.0, corrects="ee" * 32, position_id="p9")
    run.reader.dashcam.locked = False
    run.reader.dashcam.seal(LATER, SLOT_1500, RecordKind.OUTCOMES, (stray,))
    run.reader = reader(run.reader.dashcam)
    assert run.for_session(SESSIONS[2]).orphans == (stray,)


def test_rc1_is_one_of_the_two_controls_on_a_road_slot():
    _, read, _, _ = scenario()
    (path,) = read.closed_on(SESSIONS[2]).paths
    as_rc1 = replace(path, outcome=replace(path.outcome, driver_id="RC1@1"))
    as_ref = replace(path, outcome=replace(path.outcome, driver_id="REF@1"))
    controls = controls_for(path, control_nets((as_rc1, as_ref)))
    assert controls.rc1_net == path.outcome.net and controls.ref_net == path.outcome.net
    assert controls_for(path, control_nets((as_ref,))).rc1_net is None


class CountNothing:
    def verdict(self, candidate):
        return type("Verdict", (), {"counted": False})()


def test_only_counted_decisions_are_paired():
    dashcam, read, _, _ = scenario()
    decisions = sealed_decisions(dashcam, read.sessions(SESSIONS[0], SESSIONS[2]))
    cards = {code: CARDS[code] for code in ("CS1", "REF", "N0", "RC1")}
    assert CountedComparison(CountNothing(), cards, "ef" * 32).rows(decisions, ()) == ()


def test_a_damaged_decisions_file_is_listed_as_unsealed():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam)
    dashcam.damaged = frozenset({(SESSIONS[1], RecordKind.DECISIONS)})
    assert sealed_decisions(dashcam, SESSIONS).unsealed == (SESSIONS[1],)


def test_the_maximum_drawdown_is_the_deepest_fall_from_a_running_peak():
    """Daily nets 100, -300, 50, -100: equity 100 (peak), -200, -150, -250; deepest fall 100 to -250 = -350."""
    assert (
        _drawdown([100.0, -300.0, 50.0, -100.0]) == -350.0 and _drawdown([50.0, 20.0]) == 0.0 and _drawdown([]) == 0.0
    )
