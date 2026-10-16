"""One pass over the release calendars (story A20c): each calendar read whole becomes one snapshot part of
`macro-calendar/<source>` (every date it lists, with the run's time), its document kept write-once in Drive under its
SHA-256. A calendar not read, or whose last future date is under 30 days ahead, is a problem."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Protocol

from ..storage.data_store import DataStore
from ..storage.part_table import PartTable
from .model import COLUMNS, Calendar, CalendarFailed

TABLE, DOCUMENTS = "macro-calendar/{source}", "macro-calendar/documents/{source}/{sha256}.{extension}"
MIN_AHEAD = timedelta(days=30)  # MOSPI's calendar ends in March and the Fed's year in December: the next is due
LINE = "{source}: {count} dates, last {last}"
FAILED = "{source}: calendar NOT read: {error}"
STALE = "{source}: stale: its last future date is {last}, under {days} days ahead (a new calendar is due)"
NOT_SAVED = "{source}: snapshot NOT saved to Drive: {error}"


class ReleaseCalendar(Protocol):
    source: str

    def fetch(self, today: date) -> Calendar: ...


class CalendarCapture:
    def __init__(self, calendars: Sequence[ReleaseCalendar], store: DataStore,
                 clock: Callable[[], datetime] = lambda: datetime.now(UTC), out=print):  # fmt: skip
        self.calendars, self.store, self.clock, self.out = calendars, store, clock, out

    def run(self, today: date) -> list[str]:
        """Snapshots every calendar; returns the problems (one line each)."""
        problems = []
        for calendar in self.calendars:
            try:
                fetched = calendar.fetch(today)
            except (CalendarFailed, ValueError) as exc:
                problems.append(FAILED.format(source=calendar.source, error=exc))
                continue
            problems += self._keep(calendar.source, fetched, today)
        return problems

    def _keep(self, source: str, fetched: Calendar, today: date) -> list[str]:
        try:
            self._save_document(source, fetched)
            seen_at = self.clock().astimezone(UTC).isoformat()
            PartTable(self.store, TABLE.format(source=source), COLUMNS).write(
                today, [d.row(source, seen_at, fetched.period) for d in fetched.dates]
            )
        except (OSError, RuntimeError, ValueError) as exc:  # Drive (requests errors are OSError), a conflict
            return [NOT_SAVED.format(source=source, error=exc)]
        last = max((d.day for d in fetched.dates), default=today)  # an empty calendar reads as stale
        self.out(LINE.format(source=source, count=len(fetched.dates), last=last))
        return [STALE.format(source=source, last=last, days=MIN_AHEAD.days)] if last - today < MIN_AHEAD else []

    def _save_document(self, source: str, fetched: Calendar) -> None:
        digest = hashlib.sha256(fetched.document).hexdigest()
        path = DOCUMENTS.format(source=source, sha256=digest, extension=fetched.extension)
        if self.store.receipts.read(f"{self.store.area}/{path}") is None:  # an unchanged document is kept once
            self.store.put(path, fetched.document)
