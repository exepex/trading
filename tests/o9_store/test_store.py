"""Story O9 step 1: the data store parts with a local folder standing in for Drive (offline)."""

import hashlib
import subprocess
from datetime import UTC, date, datetime

import pytest

from fno.storage.data_store import DataStore, new_run_id
from fno.storage.drive_cache import DriveCache
from fno.storage.manifest_commit import GitManifestRecorder
from fno.storage.part_table import PartTable, read_parts
from fno.storage.raw_store import LocalFolderStore, RawFileConflict, RawFileStore
from fno.storage.receipts import Receipt, ReceiptFolder
from fno.storage.snapshot import latest_snapshot, write_snapshot

T0 = datetime(2026, 10, 16, 7, 30, tzinfo=UTC)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_store(tmp_path, run_id="20261016T073000Z-aaaaaa", when=T0):
    drive = LocalFolderStore(tmp_path / "drive")
    receipts = ReceiptFolder(tmp_path / "receipts")
    return DataStore(drive, "data", receipts, "test-job", run_id, clock=lambda: when), drive, receipts


def test_a_put_saves_the_bytes_in_the_drive_area_and_a_receipt_with_their_sha256(tmp_path):
    store, drive, receipts = make_store(tmp_path)
    receipt = store.put("intraday/slots/x.csv", b"rows")
    assert drive.get("data/intraday/slots/x.csv") == b"rows"
    assert receipt == Receipt("data/intraday/slots/x.csv", sha(b"rows"), 4, T0.isoformat(), "test-job",
                              "20261016T073000Z-aaaaaa")  # fmt: skip
    assert receipts.read("data/intraday/slots/x.csv") == receipt
    assert (tmp_path / "receipts/data/intraday/slots/x.csv.sha256").read_text().startswith(sha(b"rows") + "\t4\t")


def test_the_same_bytes_again_keep_the_first_receipt_and_its_time(tmp_path):
    first, _, receipts = make_store(tmp_path)
    first.put("a/b.csv", b"same")
    later, *_ = make_store(tmp_path, run_id="20261016T080000Z-bbbbbb", when=datetime(2026, 10, 16, 8, tzinfo=UTC))
    assert later.put("a/b.csv", b"same").written_at == T0.isoformat()


def test_different_bytes_at_a_saved_path_are_refused_and_nothing_changes(tmp_path):
    store, drive, receipts = make_store(tmp_path)
    store.put("a/b.csv", b"first")
    with pytest.raises(RawFileConflict):
        store.put("a/b.csv", b"other")
    assert drive.get("data/a/b.csv") == b"first" and receipts.read("data/a/b.csv").sha256 == sha(b"first")


def test_a_failed_drive_write_leaves_no_receipt(tmp_path):
    class DownDrive(RawFileStore):
        def get(self, path):
            return None

        def put(self, path, data):
            raise OSError("Drive is down")

    receipts = ReceiptFolder(tmp_path / "receipts")
    with pytest.raises(OSError):
        DataStore(DownDrive(), "data", receipts, "job", "r").put("a/b.csv", b"x")
    assert receipts.read("data/a/b.csv") is None and receipts.under("data") == []


def test_a_receipt_with_a_different_digest_is_refused(tmp_path):
    receipts = ReceiptFolder(tmp_path / "receipts")
    receipts.write(Receipt("data/a.csv", "1" * 64, 1, T0.isoformat(), "j", "r"))
    with pytest.raises(RawFileConflict):
        receipts.write(Receipt("data/a.csv", "2" * 64, 1, T0.isoformat(), "j", "r"))


def test_the_cache_downloads_only_what_it_lacks_and_checks_every_file(tmp_path):
    store, drive, receipts = make_store(tmp_path)
    store.put("t/one.csv", b"1")
    store.put("t/two.csv", b"2")
    cache = DriveCache(drive, receipts, tmp_path / "cache")
    first = cache.sync("data/t")
    assert first.complete and sorted(first.downloaded) == ["data/t/one.csv", "data/t/two.csv"]
    assert (tmp_path / "cache/data/t/one.csv").read_bytes() == b"1"
    second = cache.sync("data/t")
    assert second.present == 2 and second.downloaded == []
    (tmp_path / "cache/data/t/one.csv").write_bytes(b"tampered")
    third = cache.sync("data/t")
    assert third.downloaded == ["data/t/one.csv"] and (tmp_path / "cache/data/t/one.csv").read_bytes() == b"1"


def test_a_file_drive_does_not_return_or_returns_changed_is_reported_and_never_written(tmp_path):
    store, drive, receipts = make_store(tmp_path)
    store.put("t/kept.csv", b"good")
    store.put("t/gone.csv", b"gone")
    (tmp_path / "drive/data/t/kept.csv").write_bytes(b"changed in Drive")
    (tmp_path / "drive/data/t/gone.csv").unlink()
    report = DriveCache(drive, receipts, tmp_path / "cache").sync("data/t")
    assert not report.complete and report.downloaded == []
    assert report.problems == ["data/t/gone.csv: in the receipts, not returned by Drive",
                               "data/t/kept.csv: Drive's bytes do not match the receipt's SHA-256"]  # fmt: skip
    assert not (tmp_path / "cache/data/t").exists()


def test_a_file_without_a_receipt_is_never_read(tmp_path):
    _, drive, receipts = make_store(tmp_path)
    drive.put("data/t/unreceipted.csv", b"x")
    assert DriveCache(drive, receipts, tmp_path / "cache").sync("data/t").downloaded == []


def test_frozen_files_are_written_back_to_their_original_repository_paths(tmp_path):
    store, drive, receipts = make_store(tmp_path)
    store.put("research/forecasts/golden_iv30_rv20.csv", b"frozen bytes")
    checkout = tmp_path / "checkout"
    report = DriveCache(drive, receipts, tmp_path / "cache").sync("data/research/forecasts", into=checkout,
                                                                  strip="data/")  # fmt: skip
    assert report.complete and (checkout / "research/forecasts/golden_iv30_rv20.csv").read_bytes() == b"frozen bytes"


def test_two_runs_on_one_day_write_two_parts_and_the_table_is_their_union(tmp_path):
    columns = ("mark", "status")
    first, drive, receipts = make_store(tmp_path, run_id="20261016T073000Z-aaaaaa")
    second, *_ = make_store(tmp_path, run_id="20261016T083000Z-bbbbbb")
    PartTable(first, "intraday/slots", columns).write(date(2026, 10, 16), [{"mark": "09:15", "status": "good"}])
    PartTable(second, "intraday/slots", columns).write(date(2026, 10, 16), [{"mark": "09:30", "status": "good"}])
    DriveCache(drive, receipts, tmp_path / "cache").sync("data/intraday/slots")
    rows = read_parts(tmp_path / "cache/data/intraday/slots", columns)
    assert [r["mark"] for r in rows] == ["09:15", "09:30"]
    assert len(receipts.under("data/intraday/slots")) == 2


def test_a_part_with_other_columns_is_refused(tmp_path):
    store, *_ = make_store(tmp_path)
    PartTable(store, "t", ("a",)).write(date(2026, 10, 16), [{"a": "1"}])
    with pytest.raises(ValueError, match="columns"):
        read_parts(tmp_path / "drive/data/t", ("a", "b"))


def test_the_newest_snapshot_wins_and_older_ones_stay(tmp_path):
    older, *_ = make_store(tmp_path, run_id="20261016T073000Z-aaaaaa")
    newer, *_ = make_store(tmp_path, run_id="20261016T083000Z-bbbbbb")
    write_snapshot(newer, "paper/book1/account", {"cash": 2})
    write_snapshot(older, "paper/book1/account", {"cash": 1})
    folder = tmp_path / "drive/data/paper/book1/account"
    assert latest_snapshot(folder) == {"cash": 2} and len(list(folder.glob("*.json"))) == 2
    assert latest_snapshot(tmp_path / "nothing") is None


def test_run_ids_are_utc_stamped_unique_and_sort_by_time():
    a = new_run_id(datetime(2026, 10, 16, 7, 30, tzinfo=UTC))
    b = new_run_id(datetime(2026, 10, 16, 7, 31, tzinfo=UTC))
    assert a.startswith("20261016T073000Z-") and a < b and new_run_id(T0) != new_run_id(T0)


def git(folder, *args):
    return subprocess.run(["git", *args], cwd=folder, check=True, capture_output=True, text=True).stdout


def test_receipts_reach_main_from_a_session_branch_and_the_data_never_enters_git(tmp_path):
    origin, clone = tmp_path / "origin.git", tmp_path / "clone"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(tmp_path, "clone", "-q", str(origin), str(clone))
    for key, value in (("user.name", "t"), ("user.email", "t@example.invalid"), ("core.hooksPath", "hooks")):
        git(clone, "config", key, value)
    (clone / "README.md").write_text("x\n")
    git(clone, "add", "README.md")
    git(clone, "commit", "-q", "-m", "start")
    git(clone, "push", "-q", "origin", "HEAD:main")
    git(clone, "checkout", "-q", "-b", "claude/lucid-ptolemy-test")  # a routine container's session branch
    store = DataStore(LocalFolderStore(tmp_path / "drive"), "data", ReceiptFolder(clone / "receipts"), "job", "r1")
    store.put("intraday/slots/2026/10/16/a.csv", b"mark,status\n09:15,good\n")
    outcome = GitManifestRecorder(clone, clone / "receipts", label="receipts").commit("test")
    assert outcome == "receipts committed and pushed (1 file(s))"
    on_main = git(origin, "ls-tree", "-r", "--name-only", "main").split()
    assert "receipts/data/intraday/slots/2026/10/16/a.csv.sha256" in on_main
    assert not any(path.endswith("a.csv") for path in on_main)  # the data itself is only in Drive


@pytest.mark.parametrize(("writer", "run_id"), [("job\tx", "r"), ("job", "r\n1"), ("", "r"), ("job", "")])
def test_a_writer_or_run_id_that_would_split_a_receipt_is_refused(tmp_path, writer, run_id):
    with pytest.raises(ValueError, match="without tabs or line breaks"):
        DataStore(LocalFolderStore(tmp_path / "drive"), "data", ReceiptFolder(tmp_path / "r"), writer, run_id)


def test_a_receipt_interrupted_mid_write_is_never_read(tmp_path, monkeypatch):
    receipts = ReceiptFolder(tmp_path / "receipts")

    def crash(self, target):
        raise OSError("disk full")

    monkeypatch.setattr("pathlib.Path.replace", crash)
    with pytest.raises(OSError):
        receipts.write(Receipt("data/a.csv", "1" * 64, 1, T0.isoformat(), "j", "r"))
    monkeypatch.undo()
    assert receipts.read("data/a.csv") is None and receipts.under("data") == []
    assert [f.name for f in (tmp_path / "receipts/data").iterdir()] == [".a.csv.sha256.part"]


def test_one_receipted_file_is_synced_by_its_own_path(tmp_path):
    """A caller asking for one file gets that file, never an empty success (FL1's evening check, 23 Oct 2026)."""
    store, drive, receipts = make_store(tmp_path)
    store.put("t/one.csv", b"1")
    store.put("t/two.csv", b"2")
    report = DriveCache(drive, receipts, tmp_path / "cache").sync("data/t/one.csv")
    assert report.complete and report.downloaded == ["data/t/one.csv"]
    assert not (tmp_path / "cache/data/t/two.csv").exists()


def test_a_prefix_with_no_receipt_is_a_problem_never_an_empty_success(tmp_path):
    store, drive, receipts = make_store(tmp_path)
    store.put("t/one.csv", b"1")
    cache = DriveCache(drive, receipts, tmp_path / "cache")
    for wrong in ("data/t/none.csv", "data/elsewhere", "data/t/one"):
        report = cache.sync(wrong)
        assert not report.complete and report.present == 0 and report.downloaded == []
        assert report.problems == [f"{wrong}: no receipts under it (neither a receipted file nor a folder holding one)"]
