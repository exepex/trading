"""The seed of the weekly transcript-audit draw (owner's condition 1; judge 62 addendum 1). The week's label alone is
predictable, so a routine could know whether its session will be audited. The seed also takes NSE's official NIFTY 50
close of the week's last session, which nobody controls and nobody knows until the week is over. It is read from the
committed closes file (O6 appends each close once, from the first archived version) exactly as written. A week gets a
seed only once a later session's close is in, so its last session's close is final."""

from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass
from datetime import date
from pathlib import Path

Week = tuple[int, int]  # ISO year and week number


@dataclass(frozen=True)
class WeekSeed:
    week: str  # e.g. 2026-W43
    close_date: str  # the week's last session
    nifty_close: str  # NIFTY 50's official close that day, the file's text unchanged
    source: str  # the closes file

    @property
    def value(self) -> int:
        return int(hashlib.sha256(f"{self.week}|{self.close_date}|{self.nifty_close}".encode()).hexdigest(), 16)


def week_label(week: Week) -> str:
    return f"{week[0]}-W{week[1]:02d}"


def week_seeds(closes_file: Path, source: str) -> dict[Week, WeekSeed]:
    """Seeds of every week whose last session's close is final (a later week's close is already in the file)."""
    if not closes_file.is_file():
        return {}
    rows = csv.DictReader(io.StringIO(closes_file.read_text(encoding="utf-8")))
    last: dict[Week, tuple[str, str]] = {}
    for row in rows:
        if row["underlying"]:
            week = date.fromisoformat(row["date"]).isocalendar()[:2]
            last[week] = max(last.get(week, ("", "")), (row["date"], row["underlying"]))
    newest = max(last, default=None)
    return {w: WeekSeed(week_label(w), d, close, source) for w, (d, close) in last.items() if w != newest}
