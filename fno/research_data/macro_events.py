"""Macro release dates in A6's event model (story A20c). A6's `events.py` (frozen by experiment 1) and its hand-kept
`events.csv` are not changed: these types are apart, and the events come from A20c's captured calendar snapshots.

Point in time: a date is known from the IST day of the first snapshot that held it (its `announced_on`), but only if
that day is before the release (a date first seen on or after its day was never an announcement we saw). A future
date that a later snapshot of the same source no longer holds is withdrawn on that snapshot's day; it is then an
unscheduled event known at its old date until the withdrawal, through A6's own `known_on` (`first_announced_on`,
`first_withdrawn_on`). A date that comes back later is a new announcement."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from itertools import groupby
from zoneinfo import ZoneInfo

from .events import Event

MACRO_TYPES = ("india_cpi", "india_iip", "india_gdp", "us_fomc", "us_cpi", "us_payrolls")
IST = ZoneInfo("Asia/Kolkata")
DESCRIPTION = "{kind} (from {source}'s calendar, first seen {seen})"


def ist_day(seen_at: str) -> date:
    return datetime.fromisoformat(seen_at).astimezone(IST).date()


def macro_events(rows: Iterable[dict]) -> list[Event]:
    """Events from every captured row (columns kind, date, source, source_url, seen_at); one snapshot per (source,
    seen_at)."""
    events = []
    ordered = sorted(rows, key=lambda r: (r["source"], r["seen_at"]))
    for source, source_rows in groupby(ordered, key=lambda r: r["source"]):
        snapshots = [(ist_day(seen), {(r["kind"], date.fromisoformat(r["date"])) for r in snap})
                     for seen, snap in groupby(source_rows, key=lambda r: r["seen_at"])]  # fmt: skip
        events += _source_events(source, snapshots)
    return sorted(events, key=lambda e: (e.day, e.kind))


def _source_events(source: str, snapshots: list[tuple[date, set[tuple[str, date]]]]) -> list[Event]:
    events, live = [], {}  # live: (kind, day) -> day first seen
    for seen, dates in snapshots:
        for key in dates - live.keys():
            live[key] = seen
        for key in [k for k in live if k not in dates and k[1] > seen]:  # a future date gone: withdrawn
            events.append(_withdrawn(source, key, live.pop(key), seen))
        for key in [k for k in live if k not in dates]:  # a past date the calendar no longer covers: it stands
            events.append(_announced(source, key, live.pop(key)))
    events += [_announced(source, key, first) for key, first in live.items()]
    return [e for e in events if (e.announced_on or e.first_announced_on) < e.day]


def _announced(source: str, key: tuple[str, date], first: date) -> Event:
    kind, day = key
    return Event(day, kind, True, first, DESCRIPTION.format(kind=kind, source=source, seen=first))


def _withdrawn(source: str, key: tuple[str, date], first: date, withdrawn: date) -> Event:
    kind, day = key
    note = DESCRIPTION.format(kind=kind, source=source, seen=first) + f", withdrawn {withdrawn}"
    return Event(day, kind, False, None, note, revised_from=day, first_announced_on=first, first_withdrawn_on=withdrawn)
