"""The day's one derived row and every fixed name of story A22's files. The row is written once under a fixed name,
so a second run the same day finds it taken and a late run never hides an on-time one. Values are written only for a
part that is `ok` or `late`; any other part keeps its status and why, and its raw answer stays in Drive.
`PREOPEN_RECEIPT_BY` and `receipt_path` are what O8's witness reads (agreed with O8's owner, 21 Oct)."""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from datetime import date, time
from pathlib import Path

from ..models import IST
from ..storage.data_wiring import DATA_AREA, RECEIPTS_FOLDER
from ..storage.receipts import ReceiptFolder
from .run import LATE, OK, PartResult

PREOPEN_RECEIPT_BY = time(9, 15)  # the consumer's need: FL1's 09:15 report reads the row (O8 judges it at 17:51)
DAY_FILE = "preopen/day/{day:%Y}/{day:%m}/{day:%Y-%m-%d}.csv"
RAW_FILE = "preopen/raw/{day:%Y}/{day:%m}/{day:%d}/{part}_{seen:%H%M%S}.json"
VALUE_COLUMNS = {
    "gift": ("gift_level", "gift_contracts", "gift_expiry"),
    "fo_list": ("fo_stocks", "fo_with_iep"),
    "nifty": ("nifty_preopen",),
    "banknifty": ("banknifty_preopen",),
}
PART_COLUMNS = ("status", "reads", "seen_at", "source_time", "detail")
TIME_FORMAT = "%H:%M:%S"


def day_file(day: date) -> str:
    return DAY_FILE.format(day=day)


def raw_file(day: date, result: PartResult) -> str:
    return RAW_FILE.format(day=day, part=result.part, seen=result.answer.seen_at.astimezone(IST))


def receipt_path(day: date) -> str:
    """The committed receipt of the day row, relative to the repository."""
    return ReceiptFolder(Path(RECEIPTS_FOLDER)).file_for(f"{DATA_AREA}/{day_file(day)}").as_posix()


def columns() -> tuple[str, ...]:
    per_part = [f"{part}_{name}" for part in VALUE_COLUMNS for name in PART_COLUMNS]
    return ("date", "clock", *per_part, *(name for names in VALUE_COLUMNS.values() for name in names))


def day_row(day: date, clock: str, results: Sequence[PartResult]) -> bytes:
    row = {"date": day.isoformat(), "clock": clock}
    for result in results:
        row.update(_part_cells(result))
    out = io.StringIO()
    writer = csv.DictWriter(out, columns(), restval="", lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    return out.getvalue().encode()


def _part_cells(result: PartResult) -> dict[str, str]:
    answer = result.answer
    reading = answer.reading if answer else None
    cells = {
        "status": result.status,
        "reads": str(result.reads),
        "seen_at": f"{answer.seen_at.astimezone(IST):{TIME_FORMAT}}" if answer else "",
        "source_time": f"{reading.source_time:{TIME_FORMAT}}" if reading and reading.source_time else "",
        "detail": result.detail,
    }
    named = {f"{result.part}_{name}": value for name, value in cells.items()}
    if result.status in (OK, LATE):
        named.update(reading.values)
    return named
