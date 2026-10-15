"""A cue's derived daily table (story A17): one row per value date, append-only, with the SHA-256 of the archived copy
it came from, when we first saw it, and whether it was seen in time to be used live.

- `first_seen_at`: when the copy holding the value was fetched (IST).
- `provenance`: `live` when first seen before 09:15 IST on the first NSE session after the value date (the earliest
  open that could use it), else `backfilled`: history fetched later, never known at the time by this tool.
- A new date after the table's last one is appended. A date already held with the same value is skipped; with another
  value the table keeps its row and the change is logged in `revisions.csv` (`changed`); a date before the last one
  that the table lacks (a late publication) is logged (`late`) and never inserted. The table's bytes never change.
"""

from __future__ import annotations

import csv
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

from ..models import IST
from .collector import SourcedValue

FIELDS = ("value_date", "value", "source_sha256", "first_seen_at", "provenance")
REVISION_FIELDS = ("cue", "value_date", "kind", "table_value", "new_value", "source_sha256", "seen_at")
NSE_OPEN = time(9, 15)
LIVE, BACKFILLED = "live", "backfilled"
CHANGED, LATE = "changed", "late"


@dataclass
class MergeResult:
    added: int = 0
    revisions: int = 0  # new revision rows logged this time


def provenance(value_date: date, seen_at: datetime, next_session: Callable[[date], date]) -> str:
    """`live` when seen before the first NSE open after the value date, else `backfilled`."""
    first_use = datetime.combine(next_session(value_date), NSE_OPEN, tzinfo=IST)
    return LIVE if seen_at < first_use else BACKFILLED


class CueTable:
    def __init__(self, folder: Path, cue: str, next_session: Callable[[date], date]):
        self.folder, self.cue, self.next_session = Path(folder), cue, next_session
        self.path, self.revisions_path = self.folder / f"{cue}.csv", self.folder / "revisions.csv"

    def rows(self) -> list[dict[str, str]]:
        return _read(self.path)

    def merge(self, values: list[SourcedValue], seen_at: datetime) -> MergeResult:
        held = {r["value_date"]: r for r in self.rows()}
        logged = {_key(r["cue"], r["value_date"], r["kind"], r["new_value"]) for r in _read(self.revisions_path)}
        last = max(held, default="")
        new_rows, revisions = [], []
        for sourced in sorted(values, key=lambda s: s.value.value_date):
            day, value = sourced.value.value_date.isoformat(), sourced.value.value
            if day in held and float(held[day]["value"]) == value:
                continue
            if day in held or day < last:
                kind, table_value = (CHANGED, held[day]["value"]) if day in held else (LATE, "")
                if _key(self.cue, day, kind, value) not in logged:
                    logged.add(_key(self.cue, day, kind, value))
                    revisions.append((self.cue, day, kind, table_value, repr(value), sourced.source_sha256, seen_at))
                continue
            status = provenance(sourced.value.value_date, seen_at, self.next_session)
            new_rows.append((day, repr(value), sourced.source_sha256, seen_at.isoformat(), status))
            last = day
        _append(self.path, FIELDS, new_rows)
        _append(self.revisions_path, REVISION_FIELDS, [(*r[:-1], r[-1].isoformat()) for r in revisions])
        return MergeResult(len(new_rows), len(revisions))


def _key(cue: str, day: str, kind: str, value) -> tuple:
    return cue, day, kind, float(value)


def _read(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.read_text(encoding="utf-8").splitlines())) if path.is_file() else []


def _append(path: Path, fields: tuple[str, ...], rows: list[tuple]) -> None:
    if not rows:
        return
    new = not path.is_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        if new:
            writer.writerow(fields)
        writer.writerows(rows)
