"""O9b section 2 step 1: a repository file moves into its Drive series and reads back equal; again is a no-op; a file
that grew after its move is caught up (a table by one part of the later rows, a report by a new snapshot); a table in
Drive that is not a whole-line start of the file stops the move with nothing written."""

from __future__ import annotations

import pytest

from fno.storage.moving import MoveRefused, move_into
from fno.storage.receipted_rows import ReceiptedRowLog, ReceiptedSnapshots
from fno.storage.row_log import TableFileBroken

from .test_receipted_rows import TODAYS_FILE, Drive


@pytest.fixture
def drive(tmp_path):
    return Drive(tmp_path)


@pytest.mark.parametrize("kind", [ReceiptedRowLog, ReceiptedSnapshots])
def test_a_file_moves_reads_back_equal_and_a_second_move_writes_nothing(drive, kind):
    line = move_into(drive.series(kind, "20261022T100000Z-aaaaaa"), TODAYS_FILE, "vix.csv")
    assert line.startswith("vix.csv: moved to Drive and read back equal (") and str(len(TODAYS_FILE)) in line
    again = move_into(drive.series(kind, "20261022T110000Z-bbbbbb"), TODAYS_FILE, "vix.csv")
    assert again.startswith("vix.csv: already in Drive, equal")
    assert len(drive.receipts.under("data/vix/india_vix_daily")) == 1


def test_a_table_that_grew_after_its_move_gets_only_the_later_rows_under_the_header(drive):
    first = TODAYS_FILE.rsplit(b"2026-10-20", 1)[0]  # the file as moved, before its writer's next run
    move_into(drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa"), first, "vix.csv")
    later = drive.series(ReceiptedRowLog, "20261022T110000Z-bbbbbb")
    line = move_into(later, TODAYS_FILE, "vix.csv")
    assert line.startswith(f"vix.csv: Drive held {len(first)} bytes; caught up and read back equal")
    parts = later.files()
    assert parts == [first, b"date,close\n2026-10-20,11.50\n"] and later.rebuilt() == TODAYS_FILE


def test_a_report_that_changed_after_its_move_gets_a_new_snapshot(drive):
    move_into(drive.series(ReceiptedSnapshots, "20261022T100000Z-aaaaaa"), b"date,kind\n", "gaps.csv")
    later = drive.series(ReceiptedSnapshots, "20261022T110000Z-bbbbbb")
    assert move_into(later, TODAYS_FILE, "gaps.csv").startswith("gaps.csv: Drive held 10 bytes; caught up")
    assert later.latest_bytes() == TODAYS_FILE


def test_a_held_table_ending_mid_line_stops_the_move_by_name(drive):
    """The series never writes such a part (O9b step 2 review); one put there by hand is refused when read."""
    drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa").store.put(
        "vix/india_vix_daily/20261022T100000Z-aaaaaa.csv", TODAYS_FILE[:-3]
    )
    with pytest.raises(TableFileBroken, match="does not end with a new line"):
        move_into(drive.series(ReceiptedRowLog, "20261022T110000Z-bbbbbb"), TODAYS_FILE, "vix.csv")


def test_drive_holding_other_bytes_stops_the_move(drive):
    drive.series(ReceiptedRowLog, "20261022T100000Z-aaaaaa").write_bytes(b"date,close\n2026-10-19,1\n")
    with pytest.raises(MoveRefused, match="Drive already holds other bytes"):
        move_into(drive.series(ReceiptedRowLog, "20261022T110000Z-bbbbbb"), TODAYS_FILE, "vix.csv")
    assert len(drive.receipts.under("data/vix/india_vix_daily")) == 1  # nothing written


def test_an_empty_file_is_moved_as_an_empty_series_and_stays_equal(drive):
    assert move_into(drive.series(ReceiptedSnapshots, "r1"), b"", "level_flags.csv").startswith(
        "level_flags.csv: already in Drive, equal (0 bytes")  # fmt: skip


def test_a_move_that_reads_back_other_bytes_stops():
    class Lossy:
        """Accepts the write but gives back other bytes (a Drive copy damaged between write and read)."""

        def __init__(self):
            self.held = b""

        def current_bytes(self):
            return self.held

        def write_bytes(self, data):
            self.held = data[:-1]

        def catch_up(self, held, data):
            return data

    with pytest.raises(MoveRefused, match="read back unequal after the move"):
        move_into(Lossy(), TODAYS_FILE, "vix.csv")
