"""A4h criterion 2: each file goes write-once into Drive's `data` area with its SHA-256 receipt (O9), and which files
exist is read from the receipts; the composition root needs the Drive settings and wires NSE's public client."""

import hashlib

import pytest

from fno.close_read import wiring
from fno.close_read.reader import CloseReader
from fno.close_read.source import NseIndexList
from fno.close_read.store import DriveClosesStore
from fno.storage.data_store import DataStore
from fno.storage.raw_store import RawFileConflict
from fno.storage.receipts import ReceiptFolder
from tests.quotes.drive_fakes import FakeDrive

PATH = "closes/2026/10/2026-10-21.json"


def test_a_file_goes_to_drive_s_data_area_once_with_its_receipt(tmp_path):
    drive, receipts = FakeDrive(), ReceiptFolder(tmp_path / "receipts")
    store = DriveClosesStore(drive, DataStore(drive, "data", receipts, "closeread", "run-1"), receipts)
    sha = store.put(PATH, b"{}\n")
    assert sha == hashlib.sha256(b"{}\n").hexdigest() and drive.files == {f"data/{PATH}": b"{}\n"}
    assert store.get(PATH) == b"{}\n" and store.written() == {PATH}
    assert receipts.read(f"data/{PATH}").writer == "closeread"
    assert store.put(PATH, b"{}\n") == sha  # the same bytes again: no-op
    with pytest.raises(RawFileConflict):
        store.put(PATH, b"[]\n")


def test_the_root_refuses_without_drive_and_wires_nse_s_public_list(monkeypatch):
    monkeypatch.setattr(wiring, "build_owner_drive", lambda env: None)
    with pytest.raises(RuntimeError, match="FNO_GDRIVE"):
        wiring.build_close_reader({})
    monkeypatch.setattr(wiring, "build_owner_drive", lambda env: FakeDrive())
    monkeypatch.setattr(
        wiring, "build_data_store", lambda writer, env: DataStore(FakeDrive(), "data", None, writer, "r")
    )
    reader = wiring.build_close_reader({})
    assert isinstance(reader, CloseReader) and isinstance(reader.source, NseIndexList)
    assert isinstance(reader.store, DriveClosesStore) and reader.store.data.writer == "closeread"
