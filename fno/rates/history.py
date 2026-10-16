"""What earlier runs recorded (story A21): the table's parts and the home-page reads, read back from Drive through O9's
verified cache and the receipts, so a new run never re-records a value with a later time."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol

from ..storage.part_table import read_parts
from .constants import COLUMNS, RAW_FOLDER, TABLE
from .rows import RateRow, from_dicts

HOME_FILE = "_home.html"  # a home page that parsed; one that did not is `_home_unreadable.html`
UNREADABLE = "_unreadable"


class RatesHistory(Protocol):
    def rows(self) -> list[RateRow]: ...

    def last_home_read(self) -> datetime | None: ...


class DriveRatesHistory:
    def __init__(self, cache, receipts, area: str, into: Path):
        """`cache`: O9's DriveCache; `receipts`: its ReceiptFolder; `into`: where the table's parts land on disk."""
        self.cache, self.receipts, self.area, self.into = cache, receipts, area, Path(into)

    def rows(self) -> list[RateRow]:
        report = self.cache.sync(f"{self.area}/{TABLE}", into=self.into, strip=f"{self.area}/")
        if report.problems:
            raise RuntimeError(f"rates table not readable from Drive: {report.problems[0]}")
        return from_dicts(read_parts(self.into / TABLE, COLUMNS))

    def last_home_read(self) -> datetime | None:
        reads = [r.written_at for r in self.receipts.under(f"{self.area}/{RAW_FOLDER}") if r.path.endswith(HOME_FILE)]
        return datetime.fromisoformat(max(reads)) if reads else None
