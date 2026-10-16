"""Macro release dates in A6's event model (story A20c). A6's `events.py` (frozen by experiment 1) and its hand-kept
`events.csv` are not changed: these types are apart, and the events come from A20c's captured calendar snapshots.

Point in time: a date is known from the IST day of the first snapshot that held it (its `announced_on`), but only if
that day is before the release (a date first seen on or after its day was never an announcement we saw). A future
date that a later snapshot of the same source drops while the date lies inside that snapshot's period (the document
covers it) is withdrawn on that snapshot's day. A6 has no "cancelled" type, so a withdrawn date is A6's moved-meeting
form: `scheduled=False` with `first_announced_on` and `first_withdrawn_on`, known through `known_on` only until the
withdrawal, its description saying "WITHDRAWN". Read these events only through A6's `known_on` / `in_window`, never as
a list of things that happened. A date outside a later document's period (the next financial year's calendar) is
kept; a date that comes back after a withdrawal is a new announcement."""

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
        snapshots = [_snapshot(seen, list(snap)) for seen, snap in groupby(source_rows, key=lambda r: r["seen_at"])]
        events += _source_events(source, snapshots)
    return sorted(events, key=lambda e: (e.day, e.kind))


Snapshot = tuple[date, set[tuple[str, date]], date, date]  # seen day, (kind, day) pairs, period start and end


def _snapshot(seen_at: str, rows: list[dict]) -> Snapshot:
    pairs = {(r["kind"], date.fromisoformat(r["date"])) for r in rows}
    return (
        ist_day(seen_at),
        pairs,
        date.fromisoformat(rows[0]["period_start"]),
        date.fromisoformat(rows[0]["period_end"]),
    )


def _source_events(source: str, snapshots: list[Snapshot]) -> list[Event]:
    events, live = [], {}  # live: (kind, day) -> day first seen
    for seen, dates, start, end in snapshots:
        for key in dates - live.keys():
            live[key] = seen
        dropped = [k for k in live if k not in dates and start <= k[1] <= end]  # the document covers it
        for key in dropped:
            if key[1] > seen:  # a future date gone: withdrawn
                events.append(_withdrawn(source, key, live.pop(key), seen))
            else:  # a past date the calendar no longer lists: it stands
                events.append(_announced(source, key, live.pop(key)))
    events += [_announced(source, key, first) for key, first in live.items()]
    return [e for e in events if (e.announced_on or e.first_announced_on) < e.day]


def _announced(source: str, key: tuple[str, date], first: date) -> Event:
    kind, day = key
    return Event(day, kind, True, first, DESCRIPTION.format(kind=kind, source=source, seen=first))


def _withdrawn(source: str, key: tuple[str, date], first: date, withdrawn: date) -> Event:
    kind, day = key
    note = DESCRIPTION.format(kind=kind, source=source, seen=first) + f", WITHDRAWN {withdrawn}: no release on this day"
    return Event(day, kind, False, None, note, revised_from=day, first_announced_on=first, first_withdrawn_on=withdrawn)
