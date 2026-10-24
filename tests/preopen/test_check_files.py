"""A22d's view of its own Drive files: a receipt says a file exists (no Drive call); its bytes come only through O9's
verified cache, and a copy that differs from its receipt is refused, never read."""

from __future__ import annotations

import pytest

from fno.intraday.nse_range import read_nse_day
from fno.preopen.check_files import DriveCacheFiles, UnreadableFile
from fno.storage.data_store import DataStore
from fno.storage.drive_cache import DriveCache
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder

from .fixtures import index_close

PATH = "preopen/day/2026/10/2026-10-21.csv"


@pytest.fixture
def files(tmp_path):
    drive, receipts = LocalFolderStore(tmp_path / "drive"), ReceiptFolder(tmp_path / "receipts")
    DataStore(drive, "data", receipts, "preopen", "run-1").put(PATH, b"date\n2026-10-21\n")
    return drive, DriveCacheFiles(DriveCache(drive, receipts, tmp_path / "cache"), receipts, "data")


def test_a_receipted_file_is_there_and_reads_verified(files):
    _, view = files
    assert view.has(PATH) and view.read(PATH) == b"date\n2026-10-21\n"
    assert not view.has("preopen/day/2026/10/2026-10-20.csv")


def test_a_copy_that_differs_from_its_receipt_is_unreadable(files, tmp_path):
    drive, view = files
    (tmp_path / "drive/data" / PATH).write_bytes(b"date\n2026-10-20\n")  # changed behind the receipt
    with pytest.raises(UnreadableFile):
        view.read(PATH)


def test_nse_s_bank_row_is_read_by_its_own_name_and_nifty_stays_the_default():
    assert read_nse_day(index_close(nifty_open=1.25, bank_open=2.5), "NIFTY BANK").open == 2.5
    assert read_nse_day(index_close(nifty_open=1.25, bank_open=2.5)).open == 1.25
    with pytest.raises(ValueError, match="no NIFTY IT row"):
        read_nse_day(index_close(), "NIFTY IT")
