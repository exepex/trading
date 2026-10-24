"""REH1g (DRY2's gap G1): the rehearsal's 3 pm record lists the repository's folder (sidecars and markers) and reads a
raw quote file by name from Drive, checked against its sidecar: listed, refused when changed, empty when the day
recorded nothing."""

import hashlib
import json

import pytest

from fno.quotes.drive_only_store import RawQuoteHashMismatch
from fno.rehearsal.record_store import ListedQuoteRecord, RecordReader
from fno.storage.raw_store import LocalFolderStore

FOLDER = "groww/2026/10"
RAW = b"header\nrow\n"


def store(tmp_path, private_files):
    repository = LocalFolderStore(tmp_path / "repo")
    meta = {"snapshot_id": "nifty_20261023_145500", "csv_sha256": hashlib.sha256(RAW).hexdigest()}
    repository.put(f"{FOLDER}/nifty_20261023_145500.meta.json", json.dumps(meta).encode())
    repository.put(f"{FOLDER}/nifty_20261023.canonical", b"nifty_20261023_145500")
    private = LocalFolderStore(tmp_path / "drive")
    for name, data in private_files.items():
        private.put(f"{FOLDER}/{name}", data)
    return ListedQuoteRecord(RecordReader(repository), lambda: private, "groww", "FNO_GDRIVE_*")


def test_the_folder_lists_the_sidecar_and_marker_and_the_raw_file_reads_by_name(tmp_path):
    record = store(tmp_path, {"nifty_20261023_145500.csv": RAW})
    assert sorted(record.checksums(FOLDER)) == ["nifty_20261023.canonical", "nifty_20261023_145500.meta.json"]
    assert record.folders("groww/2026") == ["10"]
    assert record.get(f"{FOLDER}/nifty_20261023_145500.csv") == RAW


def test_a_drive_copy_that_differs_from_its_sidecar_is_refused(tmp_path):
    record = store(tmp_path, {"nifty_20261023_145500.csv": b"changed\n"})
    with pytest.raises(RawQuoteHashMismatch):
        record.get(f"{FOLDER}/nifty_20261023_145500.csv")


def test_a_day_or_month_with_nothing_recorded_lists_empty(tmp_path):
    record = store(tmp_path, {})
    assert record.checksums("groww/2026/11") == {} and record.folders("groww/2027") == []
