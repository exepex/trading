"""Story A4b, criterion 4: every reader of the 3 pm snapshots gives the same result from the Drive-only store as from
A4's single repository folder, for the same snapshot; and criterion 6: the G1 v2 live pack built from it is the same."""

import hashlib
import shutil
from datetime import date, datetime

import pytest

from fno.books.book1_inputs import LiveBook1Inputs
from fno.checks.data_checks import CaptureRecord
from fno.checks.validity_evidence import EvidenceReader
from fno.desk.execution_capture import RecorderExecutionCapture
from fno.desk.snapshot import RecordedExecutionSnapshots
from fno.desk.snapshot_inputs import SnapshotInput
from fno.forecast.capture import load_snapshot
from fno.forecast.live_pack import CUTOFF, LivePackBuilder
from fno.models import IST
from fno.quotes.compare import compare_lines
from fno.quotes.recorder import DATASET, QuoteSnapshotRecorder
from fno.quotes.report import canonical_snapshots
from fno.research_data.quote_snapshots import RecordedSnapshots
from fno.research_engine.implied_vol import Black76
from fno.research_engine.live_features import LiveAtmIvMinusRealised
from fno.storage.raw_store import LocalFolderStore
from tests.book1.test_parts import write_packs
from tests.quotes.drive_fakes import FakeDrive, split_store
from tests.quotes.test_quote_recorder import Clock, FakeProvider

DAY = date(2026, 10, 13)


def _split(old, new):
    """A4's folder `old` laid out as A4b keeps it: quote files in a fake Drive, every other file under `new`."""
    drive = FakeDrive()
    for file in (f for f in old.rglob("*") if f.is_file()):
        path = file.relative_to(old).as_posix()
        if path.endswith(".csv") and path.startswith(DATASET):
            drive.files[path] = file.read_bytes()
        else:
            (new / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(file, new / path)
    return split_store(new, drive)


@pytest.fixture
def stores(tmp_path):
    """(A4's single folder, A4b's split store) holding the same recorded day."""
    clock = Clock(datetime(2026, 10, 13, 14, 55, tzinfo=IST))
    old = LocalFolderStore(tmp_path / "old")
    QuoteSnapshotRecorder(FakeProvider(), old, clock.now, clock.sleep).record()
    new = _split(tmp_path / "old", tmp_path / "new")
    assert not list((tmp_path / "new").rglob("*.csv"))
    return old, new


def _snapshot_id(store) -> str:
    return store.get(QuoteSnapshotRecorder.path(DAY, f"nifty_{DAY:%Y%m%d}.canonical")).decode()


def test_the_forecast_capture_reads_the_same_files(stores):
    old, new = stores
    assert load_snapshot(new, DAY) == load_snapshot(old, DAY) is not None


def test_b7_s_cutoff_snapshot_is_the_same(stores):
    old, new = stores
    assert RecordedSnapshots(new).snapshot(DAY) == RecordedSnapshots(old).snapshot(DAY) is not None


def test_e2_s_common_pack_input_is_the_same(stores):
    old, new = stores
    batch = SnapshotInput(new, DATASET).collect(DAY)
    assert batch == SnapshotInput(old, DATASET).collect(DAY) and batch.items


def test_e4_s_execution_snapshot_is_the_same(stores):
    old, new = stores
    snapshot_id = _snapshot_id(old)
    assert RecordedExecutionSnapshots(new).snapshot(DAY, snapshot_id) == RecordedExecutionSnapshots(old).snapshot(
        DAY, snapshot_id
    )


def test_c4_s_evidence_is_the_same_and_still_hash_checked(stores):
    old, new = stores
    files = load_snapshot(old, DAY)
    record = CaptureRecord(files.snapshot_id, hashlib.sha256(files.csv_bytes).hexdigest(),
                           hashlib.sha256(files.meta_bytes).hexdigest(), "test")  # fmt: skip
    evidence, problems = EvidenceReader(new, DATASET).read(DAY, record)
    assert (evidence, problems) == EvidenceReader(old, DATASET).read(DAY, record) and evidence and not problems


def test_book1_s_snapshot_is_the_same(stores, tmp_path):
    old, new = stores
    files = load_snapshot(old, DAY)
    write_packs(tmp_path, DAY, files.snapshot_id, hashlib.sha256(files.csv_bytes).hexdigest(),
                meta_sha=hashlib.sha256(files.meta_bytes).hexdigest())  # fmt: skip

    def market(store):
        inputs = LiveBook1Inputs(tmp_path, store, 0.065, Black76(), lambda d, s: s, lambda m: (None, None, None),
                                 lambda d, h: dict(h))  # fmt: skip
        return inputs.day(DAY)

    assert market(new) == market(old)


def test_the_spread_report_and_the_comparison_are_the_same(stores, tmp_path):
    old, new = stores
    assert canonical_snapshots(tmp_path / "new", new) == canonical_snapshots(tmp_path / "old", old) != []
    assert compare_lines(tmp_path / "new", new) == compare_lines(tmp_path / "old", old)


class Commits:
    def __init__(self):
        self.paths = []

    def commit(self, paths, message):
        self.paths += list(paths)
        return "abc123"


def _execution_capture(tmp_path, drive):
    clock = Clock(datetime(2026, 10, 13, 15, 15, tzinfo=IST))
    store, commits = split_store(tmp_path / "quotes", drive), Commits()
    rec = QuoteSnapshotRecorder(FakeProvider(), store, clock.now, clock.sleep)
    capture = RecorderExecutionCapture(rec.capture, store, tmp_path / "quotes", tmp_path, commits)
    return capture, commits


def test_e3_s_execution_capture_commits_only_repository_files(tmp_path):
    capture, commits = _execution_capture(tmp_path, FakeDrive())
    record = capture.capture(DAY)
    assert record is not None and len(commits.paths) == 2
    assert all(path.is_file() and not path.name.endswith(".csv") for path in commits.paths)


def test_e3_s_capture_with_its_quote_file_unsaved_gives_no_record(tmp_path):
    capture, commits = _execution_capture(tmp_path, FakeDrive(down_saves=1))
    assert capture.capture(DAY) is None
    (sidecar,) = commits.paths  # the sidecar with the reason is committed; nothing raw exists to commit
    assert sidecar.name.endswith(".meta.json") and '"raw_file_saved": false' in sidecar.read_text()


def test_the_g1_v2_live_pack_is_the_same_from_drive(stores):
    """The v2 golden cases cannot be used here: their hand-built sidecars have no csv_sha256 key (frozen, and read by
    the golden tool through its own folder store), so this uses the recorded day."""
    old, new = stores
    builder = LivePackBuilder(LiveAtmIvMinusRealised(CUTOFF, 0.065, Black76()))
    coverage = {"source": "fixture", "through": "2026-10-12", "sha256": "0" * 64}

    def pack(store):
        return builder.build(DAY, load_snapshot(store, DAY), coverage, "calendar-fixture").canonical()

    assert pack(new) == pack(old)


class BrokenDrive(FakeDrive):
    def get(self, path):
        raise ConnectionError("drive unreachable on read")


def test_e3_s_capture_unreadable_from_drive_gives_no_record_and_commits_the_sidecar(tmp_path):
    drive = BrokenDrive()
    capture, commits = _execution_capture(tmp_path, drive)
    assert capture.capture(DAY) is None
    (sidecar,) = commits.paths
    assert sidecar.name.endswith(".meta.json") and list(drive.files)  # saved, but not readable back


def test_e4_s_snapshot_unreadable_from_drive_is_a_snapshot_error(stores, tmp_path):
    from fno.desk.snapshot import SnapshotError

    old, _ = stores
    broken = _split(tmp_path / "old", tmp_path / "broken")
    broken._private = BrokenDrive()  # noqa: SLF001 - Drive fails on read
    with pytest.raises(SnapshotError, match="could not be read: ConnectionError"):
        RecordedExecutionSnapshots(broken).snapshot(DAY, _snapshot_id(old))
