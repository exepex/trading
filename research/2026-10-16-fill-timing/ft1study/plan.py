"""What to fetch (PROTOCOL.md section 17): each contract any entry needs, legs and the same-expiry future, over one
window from the first decision day to the last next session that uses it, split into windows of at most 90 days."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

from .contracts import future_symbol, option_symbol
from .entries import Entry

MAX_WINDOW_DAYS = 90


@dataclass(frozen=True, order=True)
class FetchItem:
    expiry: date
    symbol: str
    start: date
    end: date


def fetch_plan(entries: Iterable[Entry]) -> list[FetchItem]:
    spans: dict[tuple[date, str], tuple[date, date]] = {}
    for entry in entries:
        symbols = [future_symbol(entry.day.expiry)]
        symbols += [option_symbol(entry.day.expiry, leg.strike, leg.kind) for leg in entry.legs or ()]
        for symbol in symbols:
            key = (entry.day.expiry, symbol)
            first, last = spans.get(key, (entry.day.day, entry.day.next_session))
            spans[key] = min(first, entry.day.day), max(last, entry.day.next_session)
    return sorted(item for (expiry, symbol), span in spans.items() for item in _split(expiry, symbol, *span))


def _split(expiry: date, symbol: str, start: date, end: date) -> list[FetchItem]:
    items = []
    while start <= end:
        last = min(end, start + timedelta(days=MAX_WINDOW_DAYS - 1))
        items.append(FetchItem(expiry, symbol, start, last))
        start = last + timedelta(days=1)
    return items
