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
# A4h-2: each index's (high, low, previous close) in the list, and the official file's day range (21 Oct) and closes
# of the previous session (19 Oct: 20 Oct is a holiday), all from NSE's real files.
RANGES = {"NIFTY 50": (23120.9, 22649.9, 22888.95), "NIFTY BANK": (55867.45, 54696.45, 55488.1),
          "INDIA VIX": (16.17, 14.18, 14.77)}  # fmt: skip
OFFICIAL_RANGES = {"Nifty 50": (23120.9, 22649.9), "Nifty Bank": (55867.45, 54696.45), "India VIX": (16.1725, 14.1825)}
PREVIOUS_DAY = date(2026, 10, 19)
PREVIOUS = {"Nifty 50": 22888.95, "Nifty Bank": 55488.1, "India VIX": 14.77}  # ind_close_all_19102026.csv


def answer(stamp="21-Oct-2026 15:30", levels=None, drop=(), ranges=None) -> dict:
    rows = [{"index": name, "last": last, "open": opened, **_range((ranges or RANGES).get(name))}
            for name, (last, opened) in (levels or LEVELS).items() if name not in drop]  # fmt: skip
    return {"timestamp": stamp, "data": [{"index": "NIFTY NEXT 50", "last": 1.0, "open": 1.0}, *rows]}


def _range(found) -> dict:
    return dict(zip(("high", "low", "previousClose"), found, strict=True)) if found else {}


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
    """`closes`: day -> official name -> close; the day range comes from `ranges` (default the real 21 Oct file's), and
    the previous session's file (19 Oct) is always there unless `previous` is False."""

    def __init__(self, closes=None, raises=None, ranges=None, previous=True):
        self.by_day = {**({PREVIOUS_DAY: PREVIOUS} if previous else {}), **(closes or {})}
        self.raises, self.ranges = raises, OFFICIAL_RANGES if ranges is None else ranges

    def values(self, day):
        if self.raises:
            raise self.raises
        if day not in self.by_day:
            return None
        values = {
            name: {"open": None, "high": None, "low": None, "close": close} for name, close in self.by_day[day].items()
        }
        for name, (high, low) in self.ranges.items():
            if name in values and day != PREVIOUS_DAY:
                values[name].update(high=high, low=low)
        return f"ind_close_all_{day:%d%m%Y}.csv", values


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
