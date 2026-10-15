"""Shared fakes for the owner-timing tests (story E8): the real NSE calendar, a set of away days, an in-memory seal
log with commit times, and the availability file's text."""

from __future__ import annotations

from datetime import date, datetime, time

from fno.config import ROOT
from fno.desk.owner_timing.availability import Availability, Seal, SealLog
from fno.models import IST
from fno.research_data.calendar import load_session_calendar

CALENDAR = load_session_calendar(ROOT / "research" / "data" / "calendar" / "nse_sessions.csv")
SALT = "salt," + "ab" * 16


def ist(day: date, hour: int, minute: int) -> datetime:
    return datetime.combine(day, time(hour, minute), IST)


class AwayDays(Availability):
    def __init__(self, *days: date):
        self.days = set(days)

    def away(self, day, as_of):
        return day in self.days


class MemorySeals(SealLog):
    """Seals with the time each one's commit reached main (None: written, never committed)."""

    def __init__(self):
        self.rows: list[tuple[Seal, datetime | None]] = []

    def sealed_before(self, moment):
        committed = [seal for seal, at in self.rows if at is not None and at < moment]
        return committed[-1] if committed else None

    def latest(self):
        return self.rows[-1][0] if self.rows else None

    def add(self, seal, sealed_at):
        self.rows.append((seal, None))  # written; a test commits it with commit_last


def calendar_file(*rows: str, newline: str = "\n") -> bytes:
    return newline.join([SALT, *rows]).encode()
