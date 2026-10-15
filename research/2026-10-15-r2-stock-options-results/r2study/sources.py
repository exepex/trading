"""Reference inputs: results meetings (NSE's list, amendment 1 D1), results filing times (A12), sectors, symbol changes
and corporate actions (Drive snapshots). Parsing only; fetching and storing are wired in `study.py`."""

from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from fno.market_read_models.corporate_actions import CorporateAction, read_corporate_actions
from fno.market_read_models.symbol_changes import SymbolChange, read_symbol_changes
from fno.models import IST

from .events import Meeting

BOARD_MEETINGS_API = "https://www.nseindia.com/api/corporate-board-meetings?index=equities&from_date={start:%d-%m-%Y}&to_date={end:%d-%m-%Y}"
MEETING_DATE_FORMAT = "%d-%b-%Y"
RIGHTS = "rights"
CORPORATE_ACTIONS_FROM = date(2025, 9, 8)  # the 13 Oct 2026 list covers the 400 days before it (manifest URL)
CORPORATE_ACTIONS_TO = date(2026, 10, 13)


def months(first: date, last: date) -> list[tuple[date, date]]:
    """Calendar months from `first` to `last`, the last one cut at `last`."""
    out, start = [], first.replace(day=1)
    while start <= last:
        following = (start + timedelta(days=32)).replace(day=1)
        out.append((start, min(following - timedelta(days=1), last)))
        start = following
    return out


def read_meetings(data: bytes) -> list[Meeting]:
    """NSE's board-meeting list (JSON array) as meetings; rows without a symbol or date are skipped."""
    out = []
    for row in json.loads(data.decode("utf-8")):
        symbol, day = (row.get("bm_symbol") or "").strip(), (row.get("bm_date") or "").strip()
        if symbol and day:
            text = f"{row.get('bm_purpose') or ''} | {row.get('bm_desc') or ''}"
            out.append(Meeting(symbol, datetime.strptime(day, MEETING_DATE_FORMAT).date(), text))
    return out


def read_filing_times(manifest: Path) -> dict[str, list[datetime]]:
    """A12's results filings: symbol -> filing times, in IST without a timezone."""
    times: dict[str, list[datetime]] = defaultdict(list)
    with manifest.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("filed_at"):
                moment = datetime.fromisoformat(row["filed_at"])
                moment = moment.astimezone(IST) if moment.tzinfo else moment
                times[row["symbol"].strip()].append(moment.replace(tzinfo=None))
    return dict(times)


def read_sectors(data: bytes) -> dict[str, str]:
    """Nifty 500 list: symbol -> `Industry`."""
    rows = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    return {r["Symbol"].strip(): r["Industry"].strip() for r in rows if r.get("Symbol")}


class SymbolNames:
    """One name per company: a session's symbol becomes the latest symbol it was renamed to after that day."""

    def __init__(self, changes: list[SymbolChange]):
        self.changes: dict[str, list[SymbolChange]] = defaultdict(list)
        for change in sorted(changes, key=lambda c: c.effective):
            self.changes[change.old].append(change)

    def __call__(self, symbol: str, day: date) -> str:
        seen = set()
        while symbol not in seen:
            seen.add(symbol)
            later = [c for c in self.changes.get(symbol, []) if c.effective > day]
            if not later:
                return symbol
            symbol, day = later[0].new, later[0].effective
        return symbol


def symbol_names(data: bytes) -> SymbolNames:
    return SymbolNames(read_symbol_changes(data, "symbolchange.csv"))


class CorporateActions:
    """Ex-dates of actions that change F&O contracts (amendment 1 D3), where NSE's list covers the dates."""

    def __init__(self, actions: list[CorporateAction], names: SymbolNames):
        self.ex_dates: dict[str, list[date]] = defaultdict(list)
        for action in actions:
            if action.changes_shares or RIGHTS in action.subject.lower():
                self.ex_dates[names(action.symbol, action.ex_date)].append(action.ex_date)

    @staticmethod
    def covers(entry: date, reaction: date) -> bool:
        return entry >= CORPORATE_ACTIONS_FROM and reaction <= CORPORATE_ACTIONS_TO

    def between(self, symbol: str, entry: date, reaction: date) -> bool:
        """An ex-date in (entry, R]."""
        return any(entry < d <= reaction for d in self.ex_dates.get(symbol, []))


def corporate_actions(data: bytes, names: SymbolNames) -> CorporateActions:
    return CorporateActions(read_corporate_actions(data, "corporate-actions-equities.json"), names)
