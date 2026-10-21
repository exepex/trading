"""Story FL1-1's records in O9's store: write-once with receipts, read back verified, a damaged copy refused."""

import pytest

from fno.forecast_lab.records import DriveReportRecords
from fno.storage.data_store import DataStore
from fno.storage.raw_store import LocalFolderStore, RawFileConflict
from fno.storage.receipts import ReceiptFolder

from .builders import DAY


@pytest.fixture
def parts(tmp_path):
    drive, receipts = LocalFolderStore(tmp_path / "drive"), ReceiptFolder(tmp_path / "receipts")
    store = DataStore(drive, "data", receipts, "lab-close", "run-1")
    return DriveReportRecords(store, receipts), drive


def test_the_report_and_its_marker_are_written_once_and_read_back(parts):
    records, drive = parts
    assert records.report(DAY) is None and not records.posted(DAY)
    records.write_report(DAY, "report\n", ["NIFTY N3: no forecast was sealed"])
    assert records.report(DAY) == ("report\n", ["NIFTY N3: no forecast was sealed"])
    records.write_report(DAY, "report\n", ["NIFTY N3: no forecast was sealed"])  # same bytes: no-op
    with pytest.raises(RawFileConflict):
        records.write_report(DAY, "another report\n", [])
    records.mark_posted(DAY, "alert sent")
    assert records.posted(DAY)
    assert drive.get("data/forecast_lab/v1/close/2026/2026-10-23.posted.json") is not None


def test_a_damaged_drive_copy_stops_the_run(parts):
    records, drive = parts
    records.write_report(DAY, "report\n", [])
    path = drive.folder / "data/forecast_lab/v1/close/2026/2026-10-23.json"
    path.write_text("tampered", encoding="utf-8")
    with pytest.raises(RuntimeError, match="cannot be read back verified"):
        records.report(DAY)
