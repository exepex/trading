"""Story A16 criteria 3, 4 and 8: the stored document (paths, UTC times, same bytes for the same document) and the
first-version store (A11's revision rule)."""

import gzip
import json
from datetime import timedelta

import pytest

from fno.intraday.document import CallRecord, SnapshotDocument, snapshot_path, utc_text
from fno.intraday.first_version_store import FirstVersionStore
from fno.storage.raw_store import AreaStore, LocalFolderStore
from tests.intraday.fakes import DAY, ist

MARK = ist(DAY, 9, 15)


def document(level=25000.5) -> SnapshotDocument:
    index = CallRecord("index", MARK, MARK + timedelta(seconds=0.8), {"last_price": level, "x": [1, 2]})
    quote = CallRecord("quote NIFTY", MARK, None, None, "GrowwAPIException", {"symbol": "NIFTY26OCT25000CE"})
    finished = MARK + timedelta(seconds=40)
    return SnapshotDocument("groww", "NIFTY", DAY, MARK, index, level, MARK - timedelta(seconds=1), quotes=[quote],
                            expected_contracts=1, failures=["quote NIFTY"], finished_at=finished)  # fmt: skip


def test_the_archive_path_follows_the_layout():
    assert snapshot_path("groww", DAY, MARK) == (
        "groww/derivatives/intraday-snapshots/2026/10/15/nifty_20261015_0915.json.gz"
    )


def test_a_document_round_trips_and_the_same_document_gives_the_same_bytes():
    data = document().to_bytes()
    assert data == document().to_bytes()  # no time in the gzip header
    back = SnapshotDocument.from_bytes(data)
    assert back.to_bytes() == data and back.recorded_contracts == 0 and back.mark == MARK


def test_every_stored_time_is_utc_with_its_offset_and_source_time_is_kept_apart():
    body = json.loads(gzip.decompress(document().to_bytes()))
    assert body["mark"] == "2026-10-15T03:45:00+00:00"
    assert body["index"]["request_sent_at"] == "2026-10-15T03:45:00+00:00"
    assert body["index_source_time"] == "2026-10-15T03:44:59+00:00" and body["finished_at"].endswith("+00:00")
    assert utc_text(None) == ""


def test_a_failed_call_keeps_only_its_exception_class_name():
    body = json.loads(gzip.decompress(document().to_bytes()))
    assert body["quotes"][0]["failure"] == "GrowwAPIException" and body["quotes"][0]["payload"] is None
    assert len(body["index"]["payload_sha256"]) == 64


def test_another_format_is_refused():
    with pytest.raises(ValueError):
        SnapshotDocument.from_bytes(gzip.compress(b'{"format": "other"}'))


def _store(tmp_path, clock=lambda: MARK):
    drive = LocalFolderStore(tmp_path / "drive")
    raw, revisions = AreaStore(drive, "raw"), AreaStore(drive, "revisions")
    return FirstVersionStore(raw, revisions, tmp_path / "revisions.csv", clock), drive


def test_saving_the_same_bytes_again_changes_nothing(tmp_path):
    store, drive = _store(tmp_path)
    path = snapshot_path("groww", DAY, MARK)
    store.put(path, b"first")
    store.put(path, b"first")
    assert store.get(path) == b"first" and store.rows() == [] and not (tmp_path / "drive" / "revisions").exists()


def test_different_bytes_go_to_the_revisions_area_and_the_raw_file_never_changes(tmp_path):
    store, drive = _store(tmp_path, clock=lambda: ist(DAY, 9, 16, 5))
    path = snapshot_path("groww", DAY, MARK)
    store.put(path, b"first")
    store.put(path, b"second")
    store.put(path, b"second")  # the same later version again: no second row
    assert store.get(path) == b"first"
    [row] = store.rows()
    assert row["path"] == path and row["size_bytes"] == "6" and row["found_at"] == "2026-10-15T03:46:05+00:00"
    assert row["revision_path"].startswith(f"{path}/20261015T091605+0530_")  # A11's name: when found, then SHA-256
    assert row["revision_path"].endswith(".json.gz")
    assert drive.get(f"revisions/{row['revision_path']}") == b"second" and store.revised == [row["revision_path"]]
