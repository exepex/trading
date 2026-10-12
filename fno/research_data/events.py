"""Scheduled market events (story A6): RBI policy decisions, Union Budgets, general-election results.

`research/data/events/events.csv` holds every event with official sources and the date its date was first publicly
announced. The experiment may only use an event that was scheduled and already announced on its decision day
(`known_on`); unscheduled events (e.g. an emergency RBI decision) are kept for the record but never usable ahead.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date

COLUMNS = (
    "date", "type", "scheduled", "announced_on", "announcement_source_url", "revised_from", "description", "source_url",
)  # fmt: skip
TYPES = ("rbi_policy", "budget", "election_result")


@dataclass(frozen=True)
class Event:
    day: date
    kind: str
    scheduled: bool
    announced_on: date | None
    description: str


def _iso(text: str, row: int, column: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"row {row}: bad {column} {text!r}") from exc


def read_events(text: str) -> list[Event]:
    """Validated events; any bad row raises with its row number (nothing is read partly)."""
    reader = csv.DictReader(io.StringIO(text))
    if tuple(reader.fieldnames or ()) != COLUMNS:
        raise ValueError(f"events columns must be {COLUMNS}")
    events = []
    for number, row in enumerate(reader, start=2):
        if row["type"] not in TYPES:
            raise ValueError(f"row {number}: unknown type {row['type']!r}")
        if row["scheduled"] not in ("yes", "no"):
            raise ValueError(f"row {number}: scheduled must be yes or no")
        if not row["source_url"].startswith("http"):
            raise ValueError(f"row {number}: missing source")
        day = _iso(row["date"], number, "date")
        scheduled = row["scheduled"] == "yes"
        announced = _iso(row["announced_on"], number, "announced_on") if row["announced_on"] else None
        if scheduled:
            if announced is None or not row["announcement_source_url"].startswith("http"):
                raise ValueError(f"row {number}: a scheduled event needs its announcement date and source")
            if announced >= day:
                raise ValueError(f"row {number}: announced on {announced}, not before the event on {day}")
        if row["revised_from"]:
            _iso(row["revised_from"], number, "revised_from")
        events.append(Event(day, row["type"], scheduled, announced, row["description"]))
    return sorted(events, key=lambda e: (e.day, e.kind))


def known_on(events: list[Event], decision_day: date) -> list[Event]:
    """Events a trader could have known about on the decision day: scheduled and announced on or before it."""
    return [e for e in events if e.scheduled and e.announced_on is not None and e.announced_on <= decision_day]


def in_window(events: list[Event], decision_day: date, start: date, end: date) -> list[Event]:
    """Known events dated after `start` and on or before `end` (the holding window)."""
    return [e for e in known_on(events, decision_day) if start < e.day <= end]
