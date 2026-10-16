"""Fakes for the monitor observer's tests (story LM1): a ledger with chosen statuses, a Drive that can be down, a
sender that can refuse, a settable clock and an open-position source."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from fno.alerts.sender import NOT_SENT, SENT, AlertSender
from fno.intraday.document import utc_text
from fno.intraday.heartbeat import Heartbeat
from fno.intraday.ledger import SlotLedger
from fno.monitor.alert_records import AlertRecords
from fno.monitor.alerting import MonitorAlerting
from fno.monitor.heartbeat import MonitorHeartbeat
from fno.monitor.limits import AlertLimits
from fno.monitor.mark_reader import MarkReader, PreviousCloses
from fno.monitor.mark_rows import MarkRows
from fno.monitor.observer import MonitorObserver
from fno.monitor.positions import OpenPositionSource
from fno.research_data.calendar import load_session_calendar
from fno.storage.index_store import LocalIndexStore
from fno.storage.wiring import CALENDAR_FILE

from .fixtures import at, settings
from .test_checks import monitor


class Closes(PreviousCloses):
    def __init__(self, value: float | None = 25000.0):
        self.value = value

    def close(self, day: date) -> float | None:
        return self.value


class Positions(OpenPositionSource):
    def __init__(self, positions=()):
        self.open = list(positions)

    def positions(self, day, mark, document):
        return list(self.open)


class Sender(AlertSender):
    def __init__(self):
        self.texts, self.refuse = [], False

    def send(self, text: str) -> str:
        self.texts.append(text)
        return NOT_SENT.format(reason="Slack refused") if self.refuse else SENT


class Drive(LocalIndexStore):
    """A local stand-in for Drive's paper area that can be switched off."""

    down = False

    def get(self, path):
        if self.down:
            raise ConnectionError("drive down")
        return super().get(path)

    def replace(self, path, data):
        if self.down:
            raise ConnectionError("drive down")
        super().replace(path, data)


class Clock:
    def __init__(self, now: datetime):
        self.now = now

    def __call__(self) -> datetime:
        return self.now + timedelta(seconds=20)


def ledger_row(day: date, hhmm: str, status: str) -> dict:
    mark = at(hhmm, day)
    return {"session": day.isoformat(), "mark": utc_text(mark), "mark_ist": hhmm, "status": status,
            "clock_skew_seconds": "0.4"}  # fmt: skip


def document(level: float):
    return SimpleNamespace(index_level=level)


class Desk:
    """One observer over a temporary intraday folder, with every fake reachable."""

    def __init__(self, tmp: Path, positions=(), closes: float | None = 25000.0):
        self.folder, self.sender, self.drive = tmp / "intraday", Sender(), Drive(tmp / "drive")
        self.ledger, self.clock, self.source = SlotLedger(self.folder), Clock(at("10:30")), Positions(positions)
        s = settings()
        reader = MarkReader(self.ledger, Closes(closes), load_session_calendar(CALENDAR_FILE), s)
        alerting = MonitorAlerting(AlertLimits(s), AlertRecords(self.drive, tmp), self.sender, s, self.clock)
        self.rows = MarkRows(self.folder / "monitor")
        self.heartbeat = Heartbeat(self.folder / "monitor")
        self.lines: list[str] = []
        self.observer = MonitorObserver(self.source, reader, monitor(), alerting, self.rows,
                                        MonitorHeartbeat(self.heartbeat), self.clock, self.lines.append)  # fmt: skip

    def mark(self, day: date, hhmm: str, status: str = "good", level: float | None = 25000.0) -> None:
        self.ledger.append(day, [ledger_row(day, hhmm, status)])
        self.clock.now = at(hhmm, day)
        self.observer.after_mark(day, at(hhmm, day), None if level is None else document(level), status)
