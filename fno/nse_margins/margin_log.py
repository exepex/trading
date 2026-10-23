"""A14's margins table as an append-only log (story A14): rows are only ever added at the end. Since O9b step 2 the
table is a write-once Drive series with receipts, read through `TableSource` and appended through `RowLog`, so the
composition root picks the place (a local file in tests).

The same row again is a no-op; any other row for an existing (structure, width, as_of) is a conflict and nothing is
written (C2 reads the latest row on or before a day, so two figures for one day would be ambiguous). The table's bytes
before an append are always a prefix of the table after it.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from datetime import date

from ..risk.margins import MARGIN_COLUMNS
from ..storage.row_log import RowLog, TableFileBroken
from ..storage.table_source import TableSource, TableUnavailable
from .rows import MarginRow


class MarginLogConflict(RuntimeError):
    """A row would contradict one already in the log; nothing was written."""


def _key(row: dict[str, str]) -> tuple[str, float, str]:
    return row["structure"], float(row["width"]), row["as_of"]


class MarginLog:
    def __init__(self, table: TableSource, log: RowLog):
        """`table`: where the rows are read; `log`: where new rows are appended (the same table)."""
        self.table, self.log = table, log

    def existing(self) -> list[dict[str, str]]:
        try:
            text = self.table.text()
        except TableUnavailable as exc:
            raise MarginLogConflict(f"{exc} (it is created with its header, never by a job)") from None
        reader = csv.DictReader(io.StringIO(text))
        if tuple(reader.fieldnames or ()) != MARGIN_COLUMNS:
            raise MarginLogConflict(f"{self.table.name}: columns must be {', '.join(MARGIN_COLUMNS)}")
        return list(reader)

    def days_from(self, source_prefix: str) -> set[date]:
        """The days that already have a row whose source starts with `source_prefix`."""
        return {date.fromisoformat(r["as_of"]) for r in self.existing() if r["source"].startswith(source_prefix)}

    def append(self, rows: Sequence[MarginRow]) -> int:
        """Adds the new rows at the end; returns how many were added. MarginLogConflict writes nothing."""
        known = {_key(r): r for r in self.existing()}
        new = []
        for row in (r.as_csv() for r in rows):
            if known.get(_key(row)) == row:
                continue
            if _key(row) in known:
                raise MarginLogConflict(f"{self.table.name} already has a different row for {_key(row)}")
            known[_key(row)] = row
            new.append(row)
        if new:
            try:
                self.log.check_appendable()
            except TableFileBroken as exc:  # a hand-edited file without its last new line: refused, never mended
                raise MarginLogConflict(str(exc)) from None
            self.log.append(MARGIN_COLUMNS, [tuple(row[c] for c in MARGIN_COLUMNS) for row in new])
        return len(new)
