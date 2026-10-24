"""Each session's instructor files are computed as of that session (judge 525; orchestrator's ruling, 23 Oct 2026):
corrections, controls and settlements sealed or known by then, never "today". A run that stopped between a Drive write
and its receipt reruns, after more records arrived, to the same bytes: a no-op write that publishes the missing
receipt. A later correction reaches a later session's file, never the earlier one's."""

import pytest

from fno.school.constants import SLOT_1500, RecordKind
from fno.school.instructor.causes.classify import Classifier
from fno.school.instructor.contracts import Modifier, record_sha256
from fno.school.instructor.fakes import FakeInstructorStore
from fno.school.instructor.outputs.run import InstructorRun
from fno.school.instructor.outputs.store import DriveInstructorStore
from fno.school.instructor.ports import InstructorKind
from tests.school.instructor.attribution.fixtures import EXPIRY
from tests.school.instructor.builders import RULES, SESSIONS, held_trade, refilled
from tests.school.instructor.causes.paths import spread_path
from tests.school.instructor.causes.test_evidence import builder, gathered
from tests.school.instructor.outputs.test_round2 import NEXT, settled_first_run
from tests.school.instructor.outputs.test_run import instructor
from tests.school.instructor.outputs.test_store import FakeData, FakePublisher, FakeReader
from tests.school.instructor.reading import LATER, WriteRefusingDashcam, correct_later, reader

SESSION = SESSIONS[2]


class Stopped(RuntimeError):
    """The run's container ends before the receipt is pushed."""


class StoppingPublisher(FakePublisher):
    def __init__(self, stop_at: str):
        super().__init__()
        self.stop_at = stop_at

    def publish(self, drive_path, what):
        if self.stop_at in what:
            raise Stopped(what)
        return super().publish(drive_path, what)


def drive_store(publisher: FakePublisher, data: FakeData | None = None) -> DriveInstructorStore:
    publisher.data = data or FakeData()
    return DriveInstructorStore(publisher.data, publisher, FakeReader(publisher.data))


def run_on(dashcam, store, settlement: float | None = None) -> InstructorRun:
    return InstructorRun(reader(dashcam), Classifier(builder(settlement=settlement), RULES), store, 0.0, RULES)


def test_a_run_stopped_before_its_receipt_reruns_after_more_records_to_the_same_bytes_and_one_receipt_each():
    dashcam = WriteRefusingDashcam()
    record = held_trade(dashcam)
    stopped = drive_store(StoppingPublisher(stop_at=InstructorKind.CAUSES))
    with pytest.raises(Stopped):
        run_on(dashcam, stopped).for_session(SESSION, write=True)
    stored = dict(stopped.data.files)
    correct_later(dashcam, record)  # more records: a correction sealed on a later session ...
    main = FakePublisher()
    main.pushed = stopped.publisher.pushed  # the attribution's receipt reached main before the stop
    rerun = run_on(dashcam, drive_store(main, stopped.data), settlement=1500.0)  # ... and the settlement published
    result = rerun.for_session(SESSION, write=True)
    assert stopped.data.files == stored  # the same bytes: no conflict, nothing rewritten
    assert sorted(path.rsplit(".", 3)[1] for path in main.pushed) == ["attribution", "causes"]  # one receipt each
    assert rerun.store.read(SESSION, InstructorKind.CAUSES) == result.classifications


def test_a_later_correction_reaches_a_later_sessions_file_never_the_earlier_sessions():
    dashcam = WriteRefusingDashcam()
    record = held_trade(dashcam)
    store = drive_store(FakePublisher())
    first = run_on(dashcam, store).for_session(SESSION, write=True)
    correct_later(dashcam, record)
    later = run_on(dashcam, store)
    assert later.for_session(SESSION) == first  # recomputed as of its own session: the same, the correction unseen
    corrected = later.for_session(LATER, write=True)
    assert [c.corrects for c in corrected.classifications] == [record_sha256(first.classifications[0])]
    assert [a.corrects for a in corrected.attributions] == [record_sha256(first.attributions[0])]


def test_the_reader_reads_corrections_sealed_up_to_the_session_it_is_given():
    dashcam = WriteRefusingDashcam()
    record = held_trade(dashcam)
    fixed = correct_later(dashcam, record)
    read = reader(dashcam)
    assert [p.outcome for p in read.closed_on(SESSION, as_of=SESSION).paths] == [record]
    assert [p.outcome for p in read.closed_on(SESSION, as_of=LATER).paths] == [fixed]
    assert [p.outcome for p in read.closed_on(SESSION).paths] == [fixed]  # no session given: up to today


def test_holding_to_expiry_counts_only_from_the_session_after_the_expiry():
    held = spread_path()
    assert gathered(held, settlement=985.0).hold_net is not None  # as of AFTER_EXPIRY, the session after it
    on_expiry = builder(settlement=985.0).build(held, None, None, EXPIRY)
    assert on_expiry.hold_net is None  # its settlement is published after that session's close


def test_a_re_check_reads_only_corrections_sealed_by_its_own_session():
    run, record, _ = settled_first_run()
    correct_later(run.reader.dashcam, record, day=NEXT, exit_price=15.0)  # sealed after the re-checking session
    later, _ = instructor(store=run.store)
    later.reader = reader(run.reader.dashcam)
    result = later.for_session(LATER, write=True)
    assert (result.attributions, result.classifications) == ((), ())  # the correction is NEXT's to find


def test_the_controls_are_read_as_of_the_session():
    dashcam = WriteRefusingDashcam()
    record = held_trade(dashcam)
    ref = refilled(record, 12.0, position_id="r1", driver_id="REF@1")  # the controls on the same road-slot
    rc1 = refilled(record, 12.0, position_id="r2", driver_id="RC1@1")
    dashcam.seal(SESSIONS[1], SLOT_1500, RecordKind.OUTCOMES, (ref, rc1))
    before = run_on(dashcam, FakeInstructorStore()).for_session(SESSION)
    assert before.classifications[0].modifier != Modifier.NOT_TESTABLE  # both controls read
    correct_later(dashcam, ref, day=LATER, exit_price=1.0)  # REF's loss corrected to a win, after the session
    assert run_on(dashcam, FakeInstructorStore()).for_session(SESSION) == before


def test_a_written_sessions_unreadable_files_are_read_as_of_that_session():
    """The already-written branch reports the outcome files it could not read as of its own session, as its first run
    did (judge 525.2's minor): a later session's damaged file is that session's to report."""
    dashcam = WriteRefusingDashcam()
    record = held_trade(dashcam)
    store = FakeInstructorStore()
    first = run_on(dashcam, store).for_session(SESSION, write=True)
    correct_later(dashcam, record)
    dashcam.damaged = frozenset({(LATER, RecordKind.OUTCOMES)})
    again = run_on(dashcam, store).for_session(SESSION, write=True)
    assert again.unreadable == first.unreadable == ()
    assert run_on(dashcam, store).for_session(LATER).unreadable == (LATER,)  # where it belongs
