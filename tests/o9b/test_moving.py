"""O9b section 2 step 1: a repository file moves into its Drive series and reads back equal; again is a no-op; Drive
holding other bytes stops the move with nothing written."""

from __future__ import annotations

import pytest

from fno.storage.moving import MoveRefused, move_into
from fno.storage.receipted_rows import ReceiptedRowLog, ReceiptedSnapshots

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

    with pytest.raises(MoveRefused, match="read back unequal after the move"):
        move_into(Lossy(), TODAYS_FILE, "vix.csv")
