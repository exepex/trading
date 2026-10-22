"""Stories FL1-1 and FL1-1d, one edition's records in O9's store: write-once with receipts, read back verified, a
damaged copy refused."""

import pytest

from fno.forecast_lab.delivery import Attachment
from fno.forecast_lab.records import DriveReportRecords
from fno.forecast_lab.written import WrittenReport
from fno.storage.data_store import DataStore
from fno.storage.raw_store import LocalFolderStore, RawFileConflict
from fno.storage.receipts import ReceiptFolder

from .builders import DAY


@pytest.fixture
def parts(tmp_path):
    drive, receipts = LocalFolderStore(tmp_path / "drive"), ReceiptFolder(tmp_path / "receipts")
    store = DataStore(drive, "data", receipts, "lab-close", "run-1")
    return DriveReportRecords(store, receipts, "forecast_lab/v1/evening"), drive


FILES = (Attachment("forecast.png", bytes(range(256)), "Today's forecast"), Attachment("f.html", b"<p>", "Details"))
REPORT = WrittenReport("report\n", ("NIFTY N3: no forecast was sealed",), ("NIFTY 2026-10-23",), ("NIFTY 2026-10-22",),
                       FILES)  # fmt: skip


def test_the_report_and_its_markers_are_written_once_and_read_back(parts):
    records, drive = parts
    assert records.report(DAY) is None and not records.posted(DAY) and not records.alerted(DAY)
    records.write_report(DAY, REPORT)
    assert records.report(DAY) == REPORT  # its coverage and its files too (binary intact): a rerun posts the same
    records.write_report(DAY, REPORT)  # same bytes: no-op
    with pytest.raises(RawFileConflict):
        records.write_report(DAY, WrittenReport("another report\n", ()))
    records.mark_posted(DAY, "alert sent")
    records.mark_alerted(DAY, ["alert NOT sent: FNO_SLACK_BOT_TOKEN is not set"])
    assert records.posted(DAY) and records.alerted(DAY)
    assert drive.get("data/forecast_lab/v1/evening/2026/2026-10-23.posted.json") is not None
    assert b"FNO_SLACK_BOT_TOKEN is not set" in drive.get("data/forecast_lab/v1/evening/2026/2026-10-23.alerted.json")


def test_a_damaged_drive_copy_stops_the_run(parts):
    records, drive = parts
    records.write_report(DAY, REPORT)
    path = drive.folder / "data/forecast_lab/v1/evening/2026/2026-10-23.json"
    path.write_text("tampered", encoding="utf-8")
    with pytest.raises(RuntimeError, match="cannot be read back verified"):
        records.report(DAY)


def test_the_evening_s_verdicts_are_kept_and_read_back(parts):
    from fno.forecast_lab.written import Verdict

    records, _ = parts
    verdict = Verdict("NIFTY", DAY, "implied", 25390.0, True, True, (25000.0, 25200.0, 25400.0, 25600.0))
    records.write_report(DAY, WrittenReport("evening\n", (), verdicts=(verdict,)))
    assert records.report(DAY).verdicts == (verdict,)
