"""O9b section 2: an append table as write-once Drive parts and a report as snapshots, written through O9's DataStore
(receipts) and read through the verified Drive cache; a table moved from the repository rebuilds byte for byte."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from fno.storage.data_store import DataStore
from fno.storage.drive_cache import DriveCache
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipted_rows import DriveDataUnavailable, PartOutOfOrder, ReceiptedRowLog, ReceiptedSnapshots
from fno.storage.receipts import ReceiptFolder
from fno.storage.row_log import TableFileBroken

TODAYS_FILE = b"date,close\n2026-10-19,11.25\n2026-10-20,11.50\n"
FIELDS = ("date", "close")


class Drive:
    def __init__(self, tmp_path):
        self.store = LocalFolderStore(tmp_path / "drive")
        self.receipts = ReceiptFolder(tmp_path / "receipts")
        self.cache_root = tmp_path / "cache"

    def series(self, kind, run_id, folder="vix/india_vix_daily"):
        store = DataStore(self.store, "data", self.receipts, "test", run_id,
                          clock=lambda: datetime(2026, 10, 22, tzinfo=UTC))  # fmt: skip
        return kind(store, DriveCache(self.store, self.receipts, self.cache_root), folder)


@pytest.fixture
def drive(tmp_path):
    return Drive(tmp_path)


def test_a_moved_table_rebuilds_byte_for_byte_and_later_runs_add_parts(drive):
    drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa").write_bytes(TODAYS_FILE)
    drive.series(ReceiptedRowLog, "20261023T100000Z-bbbbbb").append(FIELDS, [("2026-10-21", "11.75")])
    table = drive.series(ReceiptedRowLog, "20261024T100000Z-cccccc")
    assert table.rebuilt() == TODAYS_FILE + b"2026-10-21,11.75\n"
    assert [r["date"] for r in table.rows()] == ["2026-10-19", "2026-10-20", "2026-10-21"]
    assert len(drive.receipts.under("data/vix/india_vix_daily")) == 2  # one receipt per part


def test_a_run_that_adds_no_rows_writes_no_part(drive):
    drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa").append(FIELDS, [])
    assert drive.receipts.under("data/vix") == [] and drive.series(ReceiptedRowLog, "x").rows() == []


def test_two_writes_in_one_run_keep_their_order(drive):
    table = drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa")
    table.append(FIELDS, [("2026-10-19", "1")])
    table.append(FIELDS, [("2026-10-20", "2")])
    assert [r["date"] for r in table.rows()] == ["2026-10-19", "2026-10-20"]


def test_a_changed_drive_copy_stops_the_reader(drive):
    drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa").write_bytes(TODAYS_FILE)
    (drive.store.folder / "data/vix/india_vix_daily/20261022T100000Z-aaaaaa.csv").write_bytes(b"date,close\n")
    with pytest.raises(DriveDataUnavailable, match="SHA-256"):
        drive.series(ReceiptedRowLog, "x").rows()


def test_a_missing_drive_copy_stops_the_reader(drive):
    drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa").write_bytes(TODAYS_FILE)
    (drive.store.folder / "data/vix/india_vix_daily/20261022T100000Z-aaaaaa.csv").unlink()
    with pytest.raises(DriveDataUnavailable, match="not returned by Drive"):
        drive.series(ReceiptedRowLog, "x").rows()


def test_a_file_in_drive_without_a_receipt_is_never_read(drive):
    drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa").write_bytes(TODAYS_FILE)
    drive.store.put("data/vix/india_vix_daily/20261023T000000Z-zzzzzz.csv", b"date,close\n2026-10-21,99\n")
    assert len(drive.series(ReceiptedRowLog, "x").rows()) == 2


def test_snapshots_keep_every_run_and_the_newest_is_current(drive):
    folder = "vix/checks/gaps"
    assert drive.series(ReceiptedSnapshots, "x", folder).latest() == []
    drive.series(ReceiptedSnapshots, "20261022T100000Z-aaaaaa", folder).write(("date", "kind"), [("2026-10-19", "gap")])
    drive.series(ReceiptedSnapshots, "20261023T100000Z-bbbbbb", folder).write(("date", "kind"), [])
    current = drive.series(ReceiptedSnapshots, "x", folder)
    assert current.latest() == [] and current.latest_bytes() == b"date,kind\n"
    assert len(drive.receipts.under("data/vix/checks/gaps")) == 2


def test_a_file_in_the_cache_folder_without_a_receipt_is_never_read(drive):
    drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa").write_bytes(TODAYS_FILE)
    table = drive.series(ReceiptedRowLog, "x")
    table.rows()  # syncs the cache
    stray = drive.cache_root / "data/vix/india_vix_daily/20261023T000000Z-zzzzzz.csv"
    stray.write_bytes(b"date,close\n2026-10-21,99\n")
    assert table.rebuilt() == TODAYS_FILE


def test_a_part_that_would_sort_before_a_held_one_is_never_written(drive):
    """Two runs in one second (or a clock behind) would read rows out of order: the later write is refused."""
    drive.series(ReceiptedRowLog, "20261022T100000Z-bbbbbb").write_bytes(TODAYS_FILE)
    early = drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa")
    with pytest.raises(PartOutOfOrder, match="would sort before data/vix/india_vix_daily/20261022T100000Z-bbbbbb.csv"):
        early.append(FIELDS, [("2026-10-21", "11.75")])
    assert len(drive.receipts.under("data/vix/india_vix_daily")) == 1


def test_a_second_series_of_the_same_run_never_reuses_a_held_part_name(drive):
    drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa").write_bytes(TODAYS_FILE)
    with pytest.raises(PartOutOfOrder, match="would sort before"):
        drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa").append(FIELDS, [("2026-10-21", "11.75")])


def test_a_part_without_its_last_new_line_is_refused_at_read_by_name(drive):
    """Written past the series (by hand, or by an older writer): the table is never read with two rows joined."""
    series = drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa")
    series.store.put("vix/india_vix_daily/20261022T100000Z-aaaaaa.csv", TODAYS_FILE.rstrip(b"\n"))
    with pytest.raises(TableFileBroken, match="a part of vix/india_vix_daily does not end with a new line"):
        series.rows()
