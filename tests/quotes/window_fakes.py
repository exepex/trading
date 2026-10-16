"""Fakes for story A4e's named window: protocol v4's 14:30-14:40 capture in its own dataset, timed, clock-checked."""

from dataclasses import replace
from datetime import date, datetime, time, timedelta

from fno.intraday.clock import ClockCheck
from fno.models import IST
from fno.quotes.capture_log import CaptureLog, TimedLevels, TimedProvider
from fno.quotes.drive_only_store import DriveOnlyQuoteStore
from fno.quotes.market_levels import FutureLevel, LevelSource, MarketLevels
from fno.quotes.recorder import DATASET, QuoteSnapshotRecorder
from fno.quotes.slot import NIFTY_SLOT
from fno.quotes.window import QuoteWindow
from fno.server_clock import ServerClock, ServerTimeUnknown
from fno.storage.raw_store import LocalFolderStore
from tests.quotes.drive_fakes import SETTINGS, FakeDrive
from tests.quotes.test_quote_recorder import Clock, FakeProvider
from tests.quotes.test_recorder_calendar import CALENDAR

V4 = QuoteWindow("v4", time(14, 30), time(14, 40), 30 * 60)
V4_DATASET = f"{DATASET}-v4"
DAY = date(2026, 10, 13)  # a Tuesday session


def at(hour: int, minute: int, second: int = 0) -> datetime:
    return datetime(2026, 10, 13, hour, minute, second, tzinfo=IST)


class ScriptedServer(ServerClock):
    """A server whose offset from the host changes per reading (None: no trusted time; 'raise': the check itself
    fails, as a broken network stack would)."""

    def __init__(self, name, offsets, host_now):
        self.name, self.offsets, self.host_now = name, list(offsets), host_now

    def now(self):
        offset = self.offsets.pop(0) if len(self.offsets) > 1 else self.offsets[0]
        if offset == "raise":
            raise RuntimeError("network stack down")
        if offset is None:
            raise ServerTimeUnknown(f"{self.name} not reached (ConnectionError)")
        return self.host_now() + timedelta(seconds=offset)


class SlowProvider(FakeProvider):
    """Each quote answer arrives `delay` seconds after its request (the clock moves while it waits)."""

    def __init__(self, clock: Clock, delay: float, **kwargs):
        super().__init__(**kwargs)
        self.clock, self.delay = clock, delay

    def quote_book(self, chain, strike, kind):
        self.clock.sleep(self.delay)
        return super().quote_book(chain, strike, kind)


class Levels(LevelSource):
    """NSE's India VIX and futures; the answer takes `delay` seconds. NSE gives no bid or ask for the futures."""

    name = "fake-nse"

    def __init__(self, clock: Clock, delay: float = 0.0):
        self.clock, self.delay = clock, delay

    def levels(self, underlying):
        self.clock.sleep(self.delay)
        return MarketLevels(13.95, "13-Oct-2026 14:29", (FutureLevel(date(2026, 10, 27), 22010.0, 1200),))


def named_recorder(folder, start, provider=None, offsets=((0.4,), (0.6,)), level_delay=0.0, clock=None):
    """A4e's recorder as its composition root builds it, on fakes; returns (recorder, clock, drive)."""
    clock = clock or Clock(start)
    drive = FakeDrive()
    store = DriveOnlyQuoteStore(LocalFolderStore(folder), lambda: drive, V4_DATASET, SETTINGS)
    servers = [ScriptedServer(f"server{i}", o, clock.now) for i, o in enumerate(offsets)]
    log = CaptureLog(ClockCheck(servers, clock.now), clock.now, V4.end)
    recorder = QuoteSnapshotRecorder(
        TimedProvider(provider or FakeProvider(), log), store, clock.now, clock.sleep, calendar=CALENDAR,
        levels=TimedLevels(Levels(clock, level_delay), log), dataset=V4_DATASET,
        slot=replace(NIFTY_SLOT, stop_requests_at=V4.end), window=V4, log=log,
    )  # fmt: skip
    return recorder, clock, drive
