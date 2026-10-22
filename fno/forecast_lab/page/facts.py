"""Where the reasons' facts come from (story FL1-1c): a port, and the repository's own tables, A17's public cue tables
(in Drive since O9b, read through `cue_rows`) and P8's flows archive behind it. Each table is read as it stands; a
missing table gives no fact, never a guessed one."""

from __future__ import annotations

import csv
import gzip
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
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

    def problems(self) -> tuple[str, ...]:
        """Each table that could not be read so far (`<table>: <error type>`), for the page to say and alert."""
        return ()


class CueRows:
    """A17's cue tables by name, each read once (in Drive since O9b); a table that cannot be read gives no rows and is
    named in `problems` with its error type only (a message can hold paths), never skipped silently."""

    def __init__(self, tables: Callable[[], Mapping]):
        self.tables, self.problems, self._rows = tables, [], {}

    def __call__(self, cue: str) -> list[dict]:
        if cue not in self._rows:
            try:
                self._rows[cue] = self.tables()[cue].rows()
            except RuntimeError as error:  # settings missing, DriveDataUnavailable, DriveSignInRefused
                self._rows[cue] = []
                self.problems.append(f"{cue}: {type(error).__name__}")
        return self._rows[cue]


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
    def __init__(self, root: Path, flows: Callable[[date], dict[date, tuple[float, float]]], cue_rows: CueRows):
        """`flows(day)`: session -> (FII net, DII net) in Rs crore, up to `day` (P8's archive). `cue_rows`: A17's
        cue tables' rows (`value_date`, `value`)."""
        self.root, self.flows, self.cue_rows = root, flows, cue_rows

    def problems(self) -> tuple[str, ...]:
        return tuple(self.cue_rows.problems)

    def facts(self, day: date) -> Facts:
        events = {date.fromisoformat(r["date"]): EVENT_WORDS.get(r["type"], r["type"].replace("_", " "))
                  for r in _rows(self.root / EVENTS_TABLE)}  # fmt: skip
        expiries = {date.fromisoformat(r["expiry"]) for year in (day.year - 1, day.year)
                    for r in _rows(self.root / OPTIONS_PANEL.format(year=year))}  # fmt: skip
        return Facts(_series(_rows(self.root / VIX_TABLE), "date", "vix", day), events, frozenset(expiries),
                     _series(self.cue_rows(BRENT_CUE), "value_date", "value", day),
                     _series(self.cue_rows(USDINR_CUE), "value_date", "value", day), self.flows(day))  # fmt: skip
