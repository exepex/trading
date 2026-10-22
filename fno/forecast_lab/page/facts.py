"""Where the reasons' facts come from (story FL1-1c): a port, and the repository's own tables, A17's public cue tables
(in Drive since O9b, read through `cue_rows`) and P8's flows archive behind it. Each table is read as it stands; a
missing table gives no fact, never a guessed one."""

from __future__ import annotations

import csv
import gzip
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import date
from pathlib import Path

from .reasons import Facts

EVENT_WORDS = {"rbi_policy": "RBI policy decision", "budget": "Union Budget"}
VIX_TABLE = "research/data/nifty-panel/warmup_closes.csv"
EVENTS_TABLE = "research/data/events/events.csv"
OPTIONS_PANEL = "research/data/nifty-panel/options_{year}.csv.gz"
BRENT_CUE, USDINR_CUE = "brent", "usdinr_rbi"  # A17's cue names


class FactsSource(ABC):
    @abstractmethod
    def facts(self, day: date) -> Facts:
        """Every fact known by `day` (the report's day)."""


def _rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _series(rows: list[dict], day_key: str, value_key: str, day: date) -> dict[date, float]:
    out = {}
    for row in rows:
        when = date.fromisoformat(row[day_key])
        if when <= day and row.get(value_key):
            out[when] = float(row[value_key])
    return out


class RepositoryFacts(FactsSource):
    def __init__(self, root: Path, flows: Callable[[date], dict[date, tuple[float, float]]],
                 cue_rows: Callable[[str], list[dict]]):  # fmt: skip
        """`flows(day)`: session -> (FII net, DII net) in Rs crore, up to `day` (P8's archive). `cue_rows(cue)`: an A17
        cue table's rows (`value_date`, `value`), empty when the table cannot be read."""
        self.root, self.flows, self.cue_rows = root, flows, cue_rows

    def facts(self, day: date) -> Facts:
        events = {date.fromisoformat(r["date"]): EVENT_WORDS.get(r["type"], r["type"].replace("_", " "))
                  for r in _rows(self.root / EVENTS_TABLE)}  # fmt: skip
        expiries = {date.fromisoformat(r["expiry"]) for year in (day.year - 1, day.year)
                    for r in _rows(self.root / OPTIONS_PANEL.format(year=year))}  # fmt: skip
        return Facts(_series(_rows(self.root / VIX_TABLE), "date", "vix", day), events, frozenset(expiries),
                     _series(self.cue_rows(BRENT_CUE), "value_date", "value", day),
                     _series(self.cue_rows(USDINR_CUE), "value_date", "value", day), self.flows(day))  # fmt: skip
