"""F1's weekly cycles (protocol section 4). An index's expiry days are the sessions on which its options of that same
date are listed (a contract trading on its own expiry day), so weekday and holiday moves are followed as the files
show them. Each cycle enters at the close of the first regular session after the previous expiry and is held to the
next expiry; a cycle whose target date is no longer listed on its entry day (NSE re-dated it) is `moved_expiry`."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from edge1study.day_files import DayRows

MIN_SESSIONS = 2
TAKEN_CYCLE, SHORT, MOVED, NO_ENTRY_FILE = "cycle", "short_cycle", "moved_expiry", "no_entry_file"


@dataclass(frozen=True)
class WeeklyCycle:
    index: str
    previous_expiry: date
    expiry: date
    entry_day: date | None
    sessions: int  # n: regular sessions after the entry session up to and including the expiry
    status: str  # TAKEN_CYCLE or why the cycle cannot be traded


def expiry_days(rows: Sequence[DayRows]) -> list[date]:
    """The sessions on which the index's options of that very date are listed, in date order."""
    return [r.day for r in rows if any(q.expiry == r.day for q in r.options)]


def _cycle(index: str, previous: date, expiry: date, sessions: Sequence[date], by_day: dict[date, DayRows]):
    after = [d for d in sessions if previous < d <= expiry]
    if not after or after[0] == expiry:
        return WeeklyCycle(index, previous, expiry, None, 0, SHORT)
    entry, n = after[0], len(after) - 1
    if n < MIN_SESSIONS:
        return WeeklyCycle(index, previous, expiry, entry, n, SHORT)
    rows = by_day.get(entry)
    if rows is None:
        return WeeklyCycle(index, previous, expiry, entry, n, NO_ENTRY_FILE)
    if not any(q.expiry == expiry for q in rows.options):
        return WeeklyCycle(index, previous, expiry, entry, n, MOVED)
    return WeeklyCycle(index, previous, expiry, entry, n, TAKEN_CYCLE)


def weekly_cycles(index: str, rows: Sequence[DayRows], sessions: Sequence[date], first_expiry: date,
                  last_expiry: date) -> list[WeeklyCycle]:  # fmt: skip
    """One cycle per expiry from `first_expiry` to `last_expiry` (both inclusive) that has a previous expiry in the
    data; `sessions` are the regular sessions in date order."""
    by_day = {r.day: r for r in rows}
    expiries = expiry_days(rows)
    return [
        _cycle(index, previous, expiry, sessions, by_day)
        for previous, expiry in zip(expiries, expiries[1:])
        if first_expiry <= expiry <= last_expiry
    ]
