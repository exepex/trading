"""What this day already holds (story A21 part 2): every `seq_id` recorded today and every poll row, read back once per
run from today's receipted parts through O9's verified Drive cache (judge 355 SF2). A new A16 fire is a new process:
without this, it would record every item again with a later first-seen time."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Protocol

from ..storage.part_table import read_parts
from .constants import ITEM_COLUMNS, ITEMS_TABLE, OK, POLL_COLUMNS, POLLS_TABLE


class SeenSetUnreadable(RuntimeError):
    """Today's earlier parts could not be read: the run must not poll (it would re-record with later times)."""


@dataclass
class DayState:
    items: list[dict] = field(default_factory=list)  # item rows recorded today, in part order
    polls: list[dict] = field(default_factory=list)  # poll rows, in time order
    seen: set[str] = field(default_factory=set)

    def __post_init__(self):
        self.seen |= {row["seq_id"] for row in self.items}

    def last_ok(self) -> datetime | None:
        times = [datetime.fromisoformat(p["requested_at"]) for p in self.polls if p["status"] == OK]
        return max(times) if times else None

    def last_status(self) -> str | None:
        return self.polls[-1]["status"] if self.polls else None

    def kinds(self) -> set[str]:
        return {p["kind"] for p in self.polls if p["kind"]}


class DayStateSource(Protocol):
    def load(self, day: date) -> DayState: ...


class DriveDayState:
    def __init__(self, cache, area: str, into: Path):
        self.cache, self.area, self.into = cache, area, Path(into)

    def load(self, day: date) -> DayState:
        state = DayState()
        for table, columns in ((ITEMS_TABLE, ITEM_COLUMNS), (POLLS_TABLE, POLL_COLUMNS)):
            prefix = f"{table}/{day:%Y}/{day:%m}"
            report = self.cache.sync(f"{self.area}/{prefix}", into=self.into, strip=f"{self.area}/")
            if report.problems:
                raise SeenSetUnreadable(f"{table}: {report.problems[0]}")
            folder = self.into / prefix
            rows = read_parts(folder, columns) if folder.is_dir() else []
            rows = [r for r in rows if r.get("first_seen_at", r.get("requested_at", ""))[:10] == day.isoformat()]
            if table == ITEMS_TABLE:
                state.items = rows
                state.seen = {r["seq_id"] for r in rows}
            else:
                state.polls = sorted(rows, key=lambda r: r["requested_at"])
        return state
