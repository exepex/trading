"""A run that stopped between the instructor's Drive write and its receipt reaching main (story MS-INS, part e
follow-up; MS-P1j's builder, 23 Oct 2026): the rerun keeps the stored file and publishes its receipt, never computing
other records that write-once would refuse for good."""

import gzip
from datetime import date

import pytest

from fno.school.instructor.outputs.store import DriveInstructorStore, instructor_path
from fno.school.instructor.ports import InstructorConflict, InstructorKind
from fno.school.instructor.records_file import encode_instructor_file
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
    main = FakePublisher()
    main.pushed = stopped.publisher.pushed  # the attribution's receipt reached main before the stop
    rerun, _ = instructor(settlement=1500.0, store=drive_store(main, stopped.data))  # the expiry has settled since
    again = rerun.for_session(SESSIONS[2], write=True)
    assert rerun.for_session(SESSIONS[2]).classifications != again.classifications  # a recompute would differ
    assert rerun.store.data.files == stored  # the stored bytes are kept, nothing rewritten
    assert again.classifications == rerun.store.read(SESSIONS[2], InstructorKind.CAUSES)
    assert len(rerun.store.publisher.pushed) == 2  # one receipt per file, published from the stored bytes
    assert rerun.store.publisher.messages == [f"instructor causes {SESSIONS[2]} adopted: stored on Drive by a run "
                                              "stopped before its receipt"]  # fmt: skip


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


@pytest.mark.parametrize(
    ("kind", "stored"),
    [
        (InstructorKind.CAUSES, encode_instructor_file((attribution(),))),  # another kind's records
        (InstructorKind.ATTRIBUTION, b"not a gzip file"),
        (InstructorKind.ATTRIBUTION, encode_instructor_file((attribution(closed_on=date(2026, 11, 5)),))),
    ],
    ids=["another kind", "unreadable", "closed after its session"],
)
def test_a_stored_file_that_is_not_this_keys_instructor_file_is_never_adopted(kind, stored):
    kept = store()
    kept.data.files[instructor_path(DAY, kind)] = stored
    with pytest.raises(InstructorConflict, match="not adopted"):
        kept.recover(DAY, kind)
    assert kept.publisher.pushed == {}


def test_a_stored_file_not_in_canonical_form_is_never_adopted():
    kept = store()
    canonical = encode_instructor_file((attribution(),))
    kept.data.files[instructor_path(DAY, InstructorKind.ATTRIBUTION)] = gzip.compress(gzip.decompress(canonical))
    with pytest.raises(InstructorConflict, match="not canonical"):
        kept.recover(DAY, InstructorKind.ATTRIBUTION)


class RunOnlyReceipts(FakePublisher):
    """As MS-P1j's run receipts in production: a publish keeps the receipt for the run's one commit and pushes
    nothing, so `published` answers None until that commit."""

    def published(self, drive_path):
        return None


def test_a_stopped_session_is_recovered_under_run_only_receipts_without_a_conflict():
    stopped = drive_store(StoppingPublisher(stop_at=InstructorKind.CAUSES))  # both files on Drive, no causes receipt
    run, _ = instructor(store=stopped)
    with pytest.raises(Stopped):
        run.for_session(SESSIONS[2], write=True)
    stored = dict(stopped.data.files)
    rerun, _ = instructor(settlement=1500.0, store=drive_store(RunOnlyReceipts(), stopped.data))  # it would differ
    again = rerun.for_session(SESSIONS[2], write=True)
    assert stopped.data.files == stored and again.classifications  # adopted as stored: no InstructorConflict
    assert rerun.store.publisher.messages == [
        f"instructor {kind} {SESSIONS[2]} adopted: stored on Drive by a run stopped before its receipt"
        for kind in (InstructorKind.CAUSES, InstructorKind.ATTRIBUTION)
    ]


def test_stored_writes_nothing_and_answers_only_for_a_file_main_has_no_receipt_for():
    kept = drive_store(StoppingPublisher(stop_at=InstructorKind.ATTRIBUTION))
    with pytest.raises(Stopped):
        kept.write(DAY, InstructorKind.ATTRIBUTION, (attribution(),))
    files, receipts = dict(kept.data.files), dict(kept.publisher.pushed)
    assert kept.stored(DAY, InstructorKind.ATTRIBUTION) == (attribution(),)
    assert (kept.data.files, kept.publisher.pushed, kept.publisher.messages) == (files, receipts, [])
    assert kept.stored(DAY, InstructorKind.CAUSES) is None  # nothing on Drive
    kept.publisher.stop_at = "nothing"
    kept.recover(DAY, InstructorKind.ATTRIBUTION)
    assert kept.stored(DAY, InstructorKind.ATTRIBUTION) is None  # main has its receipt now
