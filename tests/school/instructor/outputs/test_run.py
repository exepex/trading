"""Part e's session run on the fake fleet (story MS-INS, criteria 1-2, 4, 6 and part a's criterion 5): attributed,
classified and written once; a rerun writes the same bytes; a classification waiting for its expiry is written again,
naming the first, once the settlement exists; the "why" line holds codes, words and rupees only; nothing is written
into the dashcam."""

from fno.school.instructor.causes.classify import Classifier
from fno.school.instructor.contracts import Cause
from fno.school.instructor.fakes import FakeInstructorStore
from fno.school.instructor.outputs.run import InstructorRun, record_sha256
from fno.school.instructor.outputs.why_line import WhyLineSource
from fno.school.instructor.ports import InstructorKind
from tests.school.contracts.builders import EXPIRY
from tests.school.instructor.builders import AFTER_EXPIRY, RULES, SESSIONS, held_trade
from tests.school.instructor.causes.test_evidence import builder
from tests.school.instructor.reading import LATER, WriteRefusingDashcam, reader


def instructor(settlement: float | None = None, store=None):
    dashcam = WriteRefusingDashcam()
    record = held_trade(dashcam)
    evidence = builder(settlement=settlement)
    run = InstructorRun(reader(dashcam), Classifier(evidence, RULES), store or FakeInstructorStore(), 0.0, RULES)
    return run, record


def test_a_session_is_attributed_classified_and_written_once():
    run, record = instructor()
    result = run.for_session(SESSIONS[2], write=True)
    assert [c.position_id for c in result.classifications] == [record.position_id] and len(result.attributions) == 1
    files = dict(run.store.files)
    run.for_session(SESSIONS[2], write=True)  # the same records: the same bytes, no conflict
    assert run.store.files == files
    assert run.store.read(SESSIONS[2], InstructorKind.CAUSES) == result.classifications


def test_a_dry_run_writes_nothing():
    run, _ = instructor()
    run.for_session(SESSIONS[2])
    assert run.store.files == {}


def test_a_classification_waiting_for_its_expiry_is_written_again_naming_the_first():
    run, _ = instructor()
    first = run.for_session(SESSIONS[2], write=True).classifications[0]
    assert Cause.EXIT_WHIPSAW in first.not_testable
    settled, _ = instructor(settlement=1500.0, store=run.store)  # the expiry has settled since
    assert settled.for_session(LATER, write=True).classifications == ()  # before the expiry: still waiting
    again = settled.for_session(AFTER_EXPIRY, write=True).classifications
    assert [c.corrects for c in again] == [record_sha256(first)]
    assert Cause.EXIT_WHIPSAW not in again[0].not_testable
    assert settled.for_session(AFTER_EXPIRY).classifications == again  # still the one correction, no third record


def test_the_why_line_names_the_driver_road_net_and_causes_and_no_contract():
    run, record = instructor()
    run.for_session(SESSIONS[2], write=True)
    (line,) = WhyLineSource(run.store).lines(SESSIONS[2])
    assert line.startswith("CS1@1 BANKNIFTY-M: net Rs ") and "why: " in line
    for leg in record.entry.legs:
        assert f"{leg.key.strike:g}" not in line and str(leg.price) not in line and leg.key.kind.value not in line
    assert EXPIRY.isoformat() not in line
    assert WhyLineSource(run.store).lines(LATER) == ()


def test_a_rerun_after_later_sessions_returns_the_session_as_written():
    """MS-P1j may finish an interrupted session late: once its causes file exists, the run returns it unchanged; and
    recomputed, as of itself, it is the same (here: the expiry has settled since)."""
    run, _ = instructor()
    first = run.for_session(SESSIONS[2], write=True)
    late, _ = instructor(settlement=1500.0, store=run.store)
    files = dict(run.store.files)
    again = late.for_session(SESSIONS[2], write=True)
    assert again.classifications == first.classifications and run.store.files == files
    assert late.for_session(SESSIONS[2]).classifications == first.classifications  # recomputed as of itself: the same
