"""Story MS-P1j (judge 523): the instructor's step reads receipts on `main` as the run fetched it and never runs a git
write (no fetch, add, commit, pull or push), so its thread can run beside the run's own committer; and its store keeps
every write until the run's own thread flushes it."""

import subprocess

import pytest

from fno.school.dashcam.publisher import RemoteReceipts
from fno.school.fleet.deferred_store import DeferredInstructorStore
from fno.school.fleet.run_receipts import RunReceipts
from fno.school.instructor.ports import InstructorConflict, InstructorKind
from fno.storage.receipts import Receipt, ReceiptFolder
from tests.school.contracts import builders as b
from tests.school.fleet.test_counts_commit import clone, git  # noqa: F401 - the real-git fixture
from tests.school.instructor.builders import attribution, classification

EARLIER, OTHER = (classification(),), (classification(primary="11"),)
DRIVE_PATH = "fno-data/school/instructor/2026/10/22.causes.jsonl.gz"
READ_ONLY = {"log", "show"}


def receipts_in(folder) -> RunReceipts:
    return RunReceipts(RemoteReceipts(ReceiptFolder(folder / "receipts"), folder))


def push_receipt(clone, tmp_path):  # noqa: F811
    """Another session pushes the receipt to the shared origin."""
    other = tmp_path / "other"
    git(tmp_path, "clone", "-q", git(clone, "remote", "get-url", "origin").strip(), str(other))
    for key, value in (("user.name", "test"), ("user.email", "test@example.invalid")):
        git(other, "config", key, value)
    ReceiptFolder(other / "receipts").write(Receipt(DRIVE_PATH, "a" * 64, 10, "2026-10-22T10:00:00+00:00", "w", "r"))
    git(other, "add", "receipts")
    git(other, "commit", "-q", "-m", "receipt")
    git(other, "push", "-q", "origin", "HEAD:main")


def test_the_step_s_lookups_and_publish_only_read_and_only_refresh_fetches(tmp_path):
    calls = []

    def run(args, **kwargs):
        calls.append(args[1])
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    receipts = RunReceipts(RemoteReceipts(ReceiptFolder(tmp_path / "receipts"), tmp_path, run=run))
    receipts.published(DRIVE_PATH)
    receipts.publish(DRIVE_PATH, "instructor causes 2026-10-22")
    assert calls and set(calls) <= READ_ONLY, calls
    calls.clear()
    git(tmp_path, "init", "-q")  # a full (not shallow) checkout: nothing to deepen
    receipts.refresh()
    assert calls == ["fetch"]


def test_a_receipt_pushed_since_the_run_s_fetch_is_seen_only_after_the_next_refresh(clone, tmp_path):  # noqa: F811
    receipts = receipts_in(clone)
    receipts.refresh()
    push_receipt(clone, tmp_path)
    assert receipts.published(DRIVE_PATH) is None, "a lookup fetched"
    receipts.refresh()
    assert receipts.published(DRIVE_PATH).sha256 == "a" * 64
    assert receipts.publish(DRIVE_PATH, "x").sha256 == "a" * 64  # an earlier run's receipt is named, nothing pushed


class RecordingStore:
    def __init__(self, written=None):
        self.written, self.calls = dict(written or {}), []

    def write(self, session, kind, records):
        if (session, kind) in self.written and self.written[(session, kind)] != records:
            raise InstructorConflict("other bytes")
        self.calls.append(kind)
        self.written[(session, kind)] = records
        return "sha"

    def read(self, session, kind):
        return self.written.get((session, kind))


def test_the_deferred_store_writes_nothing_until_flushed_and_then_in_order():
    real = RecordingStore({(b.SESSION, InstructorKind.CAUSES): EARLIER})
    store = DeferredInstructorStore(real)
    store.write(b.SESSION, InstructorKind.ATTRIBUTION, (attribution(),))
    assert real.calls == [] and store.read(b.SESSION, InstructorKind.ATTRIBUTION) == (attribution(),)
    assert store.read(b.SESSION, InstructorKind.CAUSES) == EARLIER  # what the real store holds
    store.write(b.SESSION, InstructorKind.CAUSES, EARLIER)
    store.flush()
    assert real.calls == [InstructorKind.ATTRIBUTION, InstructorKind.CAUSES]


def test_a_write_the_real_store_refuses_is_refused_at_the_flush_on_the_run_s_thread():
    store = DeferredInstructorStore(RecordingStore({(b.SESSION, InstructorKind.CAUSES): EARLIER}))
    store.write(b.SESSION, InstructorKind.CAUSES, OTHER)
    with pytest.raises(InstructorConflict):
        store.flush()
