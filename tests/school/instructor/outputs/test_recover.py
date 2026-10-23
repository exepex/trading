"""A run that stopped between the instructor's Drive write and its receipt reaching main (story MS-INS, part e
follow-up; MS-P1j's builder, 23 Oct 2026): the rerun keeps the stored file and publishes its receipt, never computing
other records that write-once would refuse for good."""

from datetime import date

import pytest

from fno.school.instructor.outputs.store import DriveInstructorStore
from fno.school.instructor.ports import InstructorKind
from tests.school.instructor.builders import SESSIONS, attribution
from tests.school.instructor.outputs.test_run import instructor
from tests.school.instructor.outputs.test_store import FakeData, FakePublisher, FakeReader, store

DAY = date(2026, 11, 4)


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


def test_a_session_stopped_before_its_receipt_is_returned_as_stored_when_a_rerun_sees_more():
    stopped = drive_store(StoppingPublisher(stop_at=InstructorKind.CAUSES))
    run, _ = instructor(store=stopped)
    with pytest.raises(Stopped):
        run.for_session(SESSIONS[2], write=True)
    stored = stopped.data.files.copy()
    rerun, _ = instructor(settlement=1500.0, store=drive_store(FakePublisher(), stopped.data))  # it would differ now
    again = rerun.for_session(SESSIONS[2], write=True)
    assert rerun.store.data.files == stored  # the stored bytes are kept, nothing rewritten
    assert again.classifications == rerun.store.read(SESSIONS[2], InstructorKind.CAUSES)
    assert len(rerun.store.publisher.pushed) == 2  # both receipts published from the stored bytes


def test_recover_publishes_a_stored_files_receipt_and_returns_its_records():
    kept = drive_store(StoppingPublisher(stop_at=InstructorKind.ATTRIBUTION))
    with pytest.raises(Stopped):
        kept.write(DAY, InstructorKind.ATTRIBUTION, (attribution(),))
    assert kept.read(DAY, InstructorKind.ATTRIBUTION) is None  # no receipt on main: a reader never trusts it
    kept.publisher.stop_at = "nothing"
    assert kept.recover(DAY, InstructorKind.ATTRIBUTION) == (attribution(),)
    assert kept.read(DAY, InstructorKind.ATTRIBUTION) == (attribution(),)


def test_recover_returns_none_when_nothing_is_stored_and_publishes_nothing():
    kept = store()
    assert kept.recover(DAY, InstructorKind.CAUSES) is None and kept.publisher.pushed == {}


def test_recover_reads_a_published_file_without_publishing_again():
    kept = drive_store(StoppingPublisher(stop_at="nothing"))
    kept.write(DAY, InstructorKind.CAUSES, (attribution(),))
    kept.publisher.stop_at = ""  # any publish now stops
    assert kept.recover(DAY, InstructorKind.CAUSES) == (attribution(),)


def test_a_run_stopped_after_its_attribution_receipts_that_file_and_computes_the_causes_on_rerun():
    stopped = drive_store(StoppingPublisher(stop_at=InstructorKind.ATTRIBUTION))
    run, _ = instructor(store=stopped)
    with pytest.raises(Stopped):
        run.for_session(SESSIONS[2], write=True)
    rerun, _ = instructor(store=drive_store(FakePublisher(), stopped.data))
    again = rerun.for_session(SESSIONS[2], write=True)
    assert rerun.store.read(SESSIONS[2], InstructorKind.ATTRIBUTION) == again.attributions
    assert rerun.store.read(SESSIONS[2], InstructorKind.CAUSES) == again.classifications
