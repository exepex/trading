"""Confirms each earlier provisional close against NSE's official file, once (a write-once `.confirm.json`): within
0.01 point "confirmed", else "differs by X" and one #fno-desk alert for NIFTY 50 or NIFTY BANK (INDIA VIX is the list's
value: its difference is recorded only). A day still unconfirmed at the second session after it alerts once. A day
that fails (the archive or Drive unreachable, a damaged file) prints one line with the error's class only and stays
unconfirmed; it never alerts on its own, and the overdue rule still applies to it (judge 447 SF1)."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, datetime, timedelta

from ..alerts.output import announce
from ..alerts.sender import AlertSender
from ..research_data.calendar import SessionCalendar
from .constants import (
    CONFIRM_LINE,
    CONFIRM_STARTS_UNTIL_SECONDS,
    DIFFERS_ALERT,
    INDICES,
    LEFT_FOR_NEXT_RUN,
    NOT_YET,
    OVERDUE,
    OVERDUE_ALERT,
    OVERDUE_SESSIONS,
    TOLERANCE,
)
from .official import OfficialCloses
from .records import confirm_path, day_of, encode, overdue_path, record_path
from .store import ClosesStore

FAILED = "close confirm {day}: not confirmed ({kind}, message withheld); tried again next run"


class Confirmer:
    def __init__(self, store: ClosesStore, official: OfficialCloses, calendar: SessionCalendar, alerts: AlertSender,
                 log: Callable[[str], None] = print, now: Callable[[], datetime] | None = None):  # fmt: skip
        self.store, self.official, self.calendar, self.alerts, self.log = store, official, calendar, alerts, log
        self.now = now

    def run(self, today: date, started: datetime | None = None) -> None:
        """`started`: when the command began; no new day starts after the time budget (the rest wait a run)."""
        written = self.store.written()
        days = sorted(d for d in map(day_of, written) if d is not None and d < today and confirm_path(d) not in written)
        for done, day in enumerate(days):
            if started is not None and self._out_of_time(started):
                self.log(LEFT_FOR_NEXT_RUN.format(count=len(days) - done))
                return
            try:
                self._confirm(day, today, written)
            except Exception as error:  # noqa: BLE001 - one day's failure never stops the others or the read
                self.log(FAILED.format(day=day, kind=type(error).__name__))
                self._overdue_quietly(day, today, written)

    def _confirm(self, day: date, today: date, written: set[str]) -> None:
        found = self.official.closes(day)
        if found is None:
            if not self._overdue(day, today, written):
                self.log(NOT_YET.format(day=day))
            return
        filename, official = found
        provisional = json.loads(self.store.get(record_path(day)))
        results = {n.listed: _status(provisional["indices"][n.listed]["last"], official.get(n.official), n.checked)
                   for n in INDICES}  # fmt: skip
        self.store.put(confirm_path(day), encode({"day": day.isoformat(), "official_file": filename,
                                                  "confirmed_on": today.isoformat(), "indices": results}))  # fmt: skip
        text = ", ".join(f"{name} {status}" for name, status in results.items())
        self.log(CONFIRM_LINE.format(day=day, results=text))
        if any(results[n.listed] != "confirmed" for n in INDICES if n.checked):
            announce(self.alerts, DIFFERS_ALERT.format(day=day, results=text))

    def _out_of_time(self, started: datetime) -> bool:
        return self.now is not None and (self.now() - started).total_seconds() >= CONFIRM_STARTS_UNTIL_SECONDS

    def _overdue(self, day: date, today: date, written: set[str]) -> bool:
        """True from the second session after the day on; the first such run writes the mark and alerts once."""
        if len(self.calendar.sessions(day + timedelta(days=1), today)) < OVERDUE_SESSIONS:
            return False
        if overdue_path(day) not in written:
            self.store.put(overdue_path(day), encode({"day": day.isoformat(), "unconfirmed_on": today.isoformat()}))
            self.log(OVERDUE.format(day=day, today=today))
            announce(self.alerts, OVERDUE_ALERT.format(day=day, today=today))
        return True

    def _overdue_quietly(self, day: date, today: date, written: set[str]) -> None:
        try:
            self._overdue(day, today, written)
        except Exception as error:  # noqa: BLE001 - Drive down too: the next run tries the mark again
            self.log(FAILED.format(day=day, kind=type(error).__name__))


def _status(provisional: float, official: float | None, checked: bool) -> str:
    if official is None:
        return "not in the official file"
    gap = abs(provisional - official)
    if gap <= TOLERANCE + 1e-9:
        return "confirmed"
    return f"differs by {gap:.2f}" + ("" if checked else " (list value)")
