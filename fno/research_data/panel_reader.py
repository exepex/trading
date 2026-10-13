"""The NIFTY panel (story A3) read back for research: every session of the manifest with its Nifty 50 and India VIX
closes, and each day's option and future rows; before the first session, the warm-up sessions (A10) with closes only.
Read-only; values are the panel's, never filled in: a session the panel left out (manifest status other than "ok")
keeps no closes and no rows."""

from __future__ import annotations

import csv
import gzip
import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from functools import cache
from pathlib import Path
from typing import NamedTuple

from ..constants import PANEL_DAY_OK
from .panel_rows import FUTURE_COLUMNS, FUTURES, OPTION_COLUMNS, OPTIONS
from .panel_store import MANIFEST_FILE, TABLE_FILE, WARMUP_FILE

O = {name: i for i, name in enumerate(OPTION_COLUMNS)}
F = {name: i for i, name in enumerate(FUTURE_COLUMNS)}


class OptionQuote(NamedTuple):
    expiry: date
    strike: float
    kind: str  # "CE" or "PE"
    close: float
    settle: float
    volume: int
    open_interest: int


class FutureQuote(NamedTuple):
    expiry: date
    close: float
    settle: float
    volume: int
    open_interest: int


class SessionClose(NamedTuple):
    day: date
    session: str  # regular, special or muhurat (the calendar's session kind)
    underlying: float | None  # Nifty 50 close; None when the panel left the day out
    vix: float | None  # India VIX close; None when the panel left the day out


@dataclass(frozen=True)
class NiftyPanel:
    sessions: tuple[SessionClose, ...]  # the warm-up sessions, then every session the manifest lists, in date order
    options: Mapping[date, tuple[OptionQuote, ...]]
    futures: Mapping[date, tuple[FutureQuote, ...]]

    def sessions_through(self, day: date) -> list[SessionClose]:
        """Sessions up to and including `day`, in date order."""
        return [s for s in self.sessions if s.day <= day]

    def session_on(self, day: date) -> SessionClose | None:
        return next((s for s in self.sessions if s.day == day), None)

    def options_on(self, day: date, expiry: date) -> list[OptionQuote]:
        return [q for q in self.options.get(day, ()) if q.expiry == expiry]

    def future_on(self, day: date, expiry: date) -> FutureQuote | None:
        return next((q for q in self.futures.get(day, ()) if q.expiry == expiry), None)


def read_nifty_panel(
    folder: Path, years: Iterable[int] | None = None, keep: Callable[[date, date], bool] | None = None
) -> NiftyPanel:
    """The panel's sessions, closes and rows for `years` (default: every year of the manifest). `keep(day, expiry)`
    limits the option rows held in memory (every year holds about 400,000 to 800,000); closes come from every row."""
    manifest = json.loads((folder / MANIFEST_FILE).read_text(encoding="utf-8"))
    wanted = set(years) if years is not None else {int(day[:4]) for day in manifest["days"]}
    options: dict[date, list[OptionQuote]] = {}
    futures: dict[date, list[FutureQuote]] = {}
    closes: dict[date, tuple[float, float]] = {}
    for year in sorted(wanted):
        for row in _rows(folder, OPTIONS, year):
            day, expiry = _day(row[O["date"]]), _day(row[O["expiry"]])
            closes.setdefault(day, (float(row[O["underlying"]]), float(row[O["vix"]])))
            if keep is None or keep(day, expiry):
                options.setdefault(day, []).append(_option(row, expiry))
        for row in _rows(folder, FUTURES, year):
            futures.setdefault(_day(row[F["date"]]), []).append(_future(row))
    sessions = tuple(
        _session(_day(day), entry, closes) for day, entry in sorted(manifest["days"].items()) if int(day[:4]) in wanted
    )
    first = min(_day(day) for day in manifest["days"])
    warmup = _warmup_sessions(folder, first) if first.year in wanted else ()
    return NiftyPanel(warmup + sessions, _frozen(options), _frozen(futures))


def _warmup_sessions(folder: Path, before: date) -> tuple[SessionClose, ...]:
    """Closes-only sessions before the panel's first session (story A10's warm-up file; none if absent): history for
    features, with no option or future rows."""
    path = folder / WARMUP_FILE
    if not path.is_file():
        return ()
    rows = csv.DictReader(path.read_text(encoding="utf-8").splitlines())
    return tuple(
        SessionClose(_day(r["date"]), r["session"], float(r["underlying"]), float(r["vix"]))
        for r in rows
        if _day(r["date"]) < before
    )


@cache
def _day(text: str) -> date:
    return date.fromisoformat(text)


def _rows(folder: Path, table: str, year: int) -> Iterable[list[str]]:
    path = folder / TABLE_FILE.format(table=table, year=year)
    if not path.is_file():
        return
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # header: the column order of panel_rows.TABLE_COLUMNS
        yield from reader


def _option(row: list[str], expiry: date) -> OptionQuote:
    return OptionQuote(
        expiry, float(row[O["strike"]]), row[O["type"]], float(row[O["close"]]),
        float(row[O["settle"]]), int(row[O["volume"]]), int(row[O["open_interest"]]),
    )  # fmt: skip


def _future(row: list[str]) -> FutureQuote:
    return FutureQuote(
        _day(row[F["expiry"]]), float(row[F["close"]]), float(row[F["settle"]]), int(row[F["volume"]]),
        int(row[F["open_interest"]]),
    )  # fmt: skip


def _session(day: date, entry: dict, closes: dict[date, tuple[float, float]]) -> SessionClose:
    underlying, vix = closes.get(day, (None, None)) if entry["status"] == PANEL_DAY_OK else (None, None)
    return SessionClose(day, entry["session"], underlying, vix)


def _frozen(rows: dict[date, list]) -> dict[date, tuple]:
    return {day: tuple(items) for day, items in rows.items()}
