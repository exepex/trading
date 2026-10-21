"""One part file per poll (story A21 part 2): O9's `PartTable` names a part by its run, and one A16 fire polls at
several marks, so each part here is `<table>/YYYY/MM/<day>.<run_id>.<HHMM>.csv`: write-once, never two writes to one
file. `read_parts` reads them like any other part."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date, datetime

from ..storage.part_table import PART_SUFFIX, part_bytes


class MarkParts:
    def __init__(self, store, table: str, columns: Sequence[str]):
        self.store, self.table, self.columns = store, table, tuple(columns)

    def write(self, day: date, mark: datetime, rows: Iterable[dict]):
        path = f"{self.table}/{day:%Y}/{day:%m}/{day:%Y-%m-%d}.{self.store.run_id}.{mark:%H%M}{PART_SUFFIX}"
        return self.store.put(path, part_bytes(self.columns, rows))
