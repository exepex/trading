"""Extends the India VIX table from the month files first archived in Drive (story A15).

Months are added in order after the table's last day. The first month not in the archive, or failing the check,
stops the extension there and is named: later months wait, so the table never has a hole filled from behind.
The bytes are always the raw area's original file, never a later revision (A11 keeps those apart).
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime

from ..storage.raw_store import RawFileStore
from .month_file import VixMonthReader
from .source import month_start
from .table import VixDailyTable, VixRow


@dataclass
class TableExtension:
    added: int = 0
    stopped_at: str = ""  # why the table stops before a month; empty when every month asked for is in

    def lines(self, table: VixDailyTable) -> list[str]:
        line = f"India VIX table: {self.added} days added, last day {table.last_day()}"
        return [line] + ([f"table STOPPED: {self.stopped_at}"] if self.stopped_at else [])


class VixTableBuilder:
    def __init__(
        self,
        archive: RawFileStore,
        path_for: Callable[[date], str],
        reader: VixMonthReader,
        table: VixDailyTable,
        clock: Callable[[], datetime],
    ):
        self.archive, self.path_for, self.reader, self.table, self.clock = archive, path_for, reader, table, clock

    def extend(self, months: list[date]) -> TableExtension:
        result, last = TableExtension(), self.table.last_day()
        for month in months:
            if last is not None and month < month_start(last):
                continue  # already in the table
            problem = self._add(month, result)
            if problem:
                result.stopped_at = f"{month:%Y-%m}: {problem}"
                break
        return result

    def _add(self, month: date, result: TableExtension) -> str | None:
        path = self.path_for(month)
        data = self.archive.get(path)
        if data is None:
            return "not in the archive"
        try:
            days = self.reader.read(data, month)
        except ValueError as exc:
            return f"archived file fails the check: {exc}"
        sha256, seen = hashlib.sha256(data).hexdigest(), self.clock()
        result.added += self.table.append([VixRow(day, path, sha256, seen) for day in days])
        return None
