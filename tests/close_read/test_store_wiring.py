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


class Reader:
    def __init__(self, code):
        self.code, self.which = code, None

    def run(self, which):
        self.which = which
        return self.code


class Committer:
    def __init__(self, line):
        self.line, self.calls = line, 0

    def commit(self, what):
        self.calls += 1
        return self.line


def _cli(monkeypatch, commit, line="close-read receipts committed and pushed (2 file(s))", code=0, recheck=False):
    from argparse import Namespace

    from fno.close_read.cli import cmd_closes

    reader, committer, out = Reader(code), Committer(line), []
    monkeypatch.setattr(wiring, "build_close_reader", lambda: reader)
    monkeypatch.setattr(wiring, "build_receipts_committer", lambda: committer)
    result = cmd_closes(Namespace(recheck=recheck, commit=commit), out.append)
    return result, reader.which, committer.calls, out


def test_o1_s_run_commits_nothing_itself_and_a_hand_run_commits_a4h_s_receipts_only(monkeypatch):
    """Judge 447 minor: a hand run's receipts reach main, so the next run sees them and never writes again."""
    assert _cli(monkeypatch, commit=False) == (0, "first", 0, [])
    assert _cli(monkeypatch, commit=True, recheck=True)[1:3] == ("recheck", 1)
    failed = "close-read receipts NOT committed: push failed: rejected. Commit receipts/data/closes/ by hand"
    assert _cli(monkeypatch, commit=True, line=failed)[0] == 1


def test_the_hand_run_s_committer_owns_a4h_s_receipts_folder_only():
    committer = wiring.build_receipts_committer()
    assert committer.folder == "receipts/data/closes" and committer.label == "close-read receipts"
