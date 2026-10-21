"""Confirms each earlier provisional close against NSE's official file, once (a write-once `.confirm.json`): within
0.01 point "confirmed", else "differs by X" and one #fno-desk alert for NIFTY 50 or NIFTY BANK (INDIA VIX is the list's
value: its difference is recorded only). A day still unconfirmed at the second session after it alerts once."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, timedelta

from ..alerts.output import announce
from ..alerts.sender import AlertSender
from ..fo_bhavcopy import BadFile
from ..research_data.calendar import SessionCalendar
from .constants import (
    CONFIRM_LINE,
    DIFFERS_ALERT,
    INDICES,
    NOT_YET,
    OVERDUE,
    OVERDUE_ALERT,
    OVERDUE_SESSIONS,
    TOLERANCE,
)
from .official import OfficialCloses
from .records import confirm_path, day_of, encode, overdue_path, record_path
from .store import ClosesStore

UNREADABLE = "close confirm {day}: the official file {problem}; not confirmed"


class Confirmer:
    def __init__(self, store: ClosesStore, official: OfficialCloses, calendar: SessionCalendar, alerts: AlertSender,
                 log: Callable[[str], None] = print):  # fmt: skip
        self.store, self.official, self.calendar, self.alerts, self.log = store, official, calendar, alerts, log

    def run(self, today: date) -> None:
        written = self.store.written()
        days = sorted(d for d in map(day_of, written) if d is not None and d < today)
        for day in (d for d in days if confirm_path(d) not in written):
            self._confirm(day, today, written)

    def _confirm(self, day: date, today: date, written: set[str]) -> None:
        try:
            found = self.official.closes(day)
        except BadFile:
            self.log(UNREADABLE.format(day=day, problem="cannot be read"))
            return
        if found is None:
            self._not_yet(day, today, written)
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

    def _not_yet(self, day: date, today: date, written: set[str]) -> None:
        if len(self.calendar.sessions(day + timedelta(days=1), today)) < OVERDUE_SESSIONS:
            self.log(NOT_YET.format(day=day))
            return
        if overdue_path(day) in written:
            return  # alerted once already
        self.store.put(overdue_path(day), encode({"day": day.isoformat(), "unconfirmed_on": today.isoformat()}))
        self.log(OVERDUE.format(day=day, today=today))
        announce(self.alerts, OVERDUE_ALERT.format(day=day, today=today))


def _status(provisional: float, official: float | None, checked: bool) -> str:
    if official is None:
        return "not in the official file"
    gap = abs(provisional - official)
    if gap <= TOLERANCE + 1e-9:
        return "confirmed"
    return f"differs by {gap:.2f}" + ("" if checked else " (list value)")
