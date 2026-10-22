"""Story A4h's fakes: NSE answers built from the 21 Oct 2026 read, a write-once memory store, the official file, a
calendar with a holiday, a special and a muhurat day, a clock and an alert sender."""

from __future__ import annotations

import hashlib
from datetime import date, datetime

from fno.alerts.sender import SENT, AlertSender
from fno.close_read.confirm import Confirmer
from fno.close_read.official import OfficialCloses
from fno.close_read.reader import CloseReader
from fno.close_read.source import CloseListSource
from fno.close_read.store import ClosesStore
from fno.models import IST
from fno.research_data.calendar import CsvSessionCalendar
from fno.storage.raw_store import RawFileConflict

DAY = date(2026, 10, 21)  # a Wednesday, a regular session
SPECIAL, MUHURAT, HOLIDAY = date(2026, 10, 24), date(2026, 11, 8), date(2026, 10, 20)
CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n"
    "2026-10-20,holiday,Dussehra,https://example.test\n"
    "2026-10-24,special,Sat special session,https://example.test\n"
    "2026-11-08,muhurat,Diwali muhurat,https://example.test\n"
)
LEVELS = {"NIFTY 50": (22811.35, 23016.0), "NIFTY BANK": (54976.9, 55707.85), "INDIA VIX": (15.7, 14.77)}
OFFICIAL = {"Nifty 50": 22811.35, "Nifty Bank": 54976.9, "India VIX": 15.68}  # ind_close_all_21102026.csv


def answer(stamp="21-Oct-2026 15:30", levels=None, drop=()) -> dict:
    rows = [{"index": name, "last": last, "open": opened, "previousClose": 1.0}
            for name, (last, opened) in (levels or LEVELS).items() if name not in drop]  # fmt: skip
    return {"timestamp": stamp, "data": [{"index": "NIFTY NEXT 50", "last": 1.0, "open": 1.0}, *rows]}


def at(hour, minute, day=DAY) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=IST)


class Answers(CloseListSource):
    """Each call takes the next item: an answer dict, or an exception to raise."""

    def __init__(self, *items):
        self.items, self.calls = list(items), 0

    def answer(self):
        item = self.items[min(self.calls, len(self.items) - 1)]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return item, repr(item).encode()


class MemoryStore(ClosesStore):
    def __init__(self):
        self.files: dict[str, bytes] = {}

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data):
        if path in self.files and self.files[path] != data:
            raise RawFileConflict(path)
        self.files[path] = data
        return hashlib.sha256(data).hexdigest()

    def written(self):
        return set(self.files)


class Official(OfficialCloses):
    def __init__(self, closes=None, raises=None):
        self.by_day, self.raises = dict(closes or {}), raises

    def closes(self, day):
        if self.raises:
            raise self.raises
        return (f"ind_close_all_{day:%d%m%Y}.csv", self.by_day[day]) if day in self.by_day else None


class Alerts(AlertSender):
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return SENT


class Clock:
    def __init__(self, now):
        self.now_at, self.slept = now, []

    def now(self):
        return self.now_at

    def sleep(self, seconds):
        self.slept.append(seconds)


def reader(store, source, clock, official=None, alerts=None, lines=None):
    log = lines.append if lines is not None else print
    confirmer = Confirmer(store, official or Official(), CALENDAR, alerts or Alerts(), log, clock.now)
    return CloseReader(source, store, confirmer, CALENDAR, clock.now, clock.sleep, log)
