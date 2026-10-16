"""Story O2: the fakes of the daily run's outside services, and only those: the owner's Drive, Slack, Groww's market
data, NSE's archive, the clock, and the child commands (NIFTY's 3 pm part and the 15:15 capture run A4's real recorder
over the fake Groww; Book 1's decision runs the real Book 1). Every one has a switch for its family's failure."""

from __future__ import annotations

import math
import traceback
from datetime import date, datetime, timedelta

from fno.alerts.sender import AlertSender
from fno.constants import OPTION_CALL, OPTION_PUT
from fno.daily.processes import Process, Processes
from fno.models import IST, OptionChain, OptionQuote, QuoteBook
from fno.quotes.recorder import NSE_DATASET, QuoteSnapshotRecorder
from fno.storage.raw_store import RawFileConflict, RawFileStore
from tests.desk.builders import LOT, fly_rows, write_snapshot

START = datetime(2026, 10, 14, 14, 33, tzinfo=IST)  # the routine's start (CLAUDE.md)
DAY = START.date()


def previous_close() -> float:
    """NIFTY's committed close of the session before the fixture day (C3 checks the spot against it)."""
    from fno.forecast.closes_source import CommittedClosesFile
    from fno.storage.wiring import PANEL_FOLDER
    from tests.checks.builders import CALENDAR

    rows = CommittedClosesFile(PANEL_FOLDER / "warmup_closes.csv").closes().rows
    return rows[CALENDAR.previous_session(DAY)][0]


SPOT = round(previous_close() + 5.0, 2)  # the day's level, a quiet move from the previous close


def market_rows(at: datetime) -> list[dict]:
    """The fixture fly's four quotes as a capture at `at` records them, NIFTY's level on every row."""
    return [r | {"spot": f"{SPOT:g}", "response_received_at": at.isoformat()} for r in fly_rows()]


class GrowwDown(ConnectionError):
    """What the Groww SDK raises when Groww cannot be reached."""


class FixtureProvider:
    """Groww's market data for the fixture day: NIFTY at `SPOT`, five expiries, a smooth chain 600 points either
    side; `down` fails every call, as a Groww outage does. Read-only, as the real adapter: there is no order call."""

    name = "groww"
    EXPIRIES = (date(2026, 10, 20), date(2026, 10, 27), date(2026, 11, 3), date(2026, 11, 24), date(2026, 12, 29))

    def __init__(self, clock: FakeClock):
        self.clock, self.down = clock, False

    def expiries(self, underlying):
        self._reachable()
        return list(self.EXPIRIES)

    def chain(self, underlying, expiry):
        self._reachable()
        centre = round(SPOT / 50) * 50
        quotes = {(k, t): OptionQuote(k, t, price(k, t, expiry), symbol=symbol(k, t, expiry))
                  for k in (centre + 50 * i for i in range(-12, 13)) for t in (OPTION_CALL, OPTION_PUT)}  # fmt: skip
        return OptionChain(underlying, SPOT, expiry, self.clock(), LOT, quotes)

    def quote_book(self, chain, strike, kind):
        self._reachable()
        mid = price(strike, kind, chain.expiry)
        name = symbol(strike, kind, chain.expiry)
        return QuoteBook(name, mid - 0.5, mid + 0.5, 650, 650, mid, self.clock(), "fields", "h")

    def _reachable(self):
        if self.down:
            raise GrowwDown("groww unreachable (HTTP 503)")


def symbol(strike: float, kind: str, expiry: date) -> str:
    return f"NIFTY{expiry:%y%m%d}{strike:g}{kind}"


def price(strike: float, kind: str, expiry: date) -> float:
    """Intrinsic value plus a time value that falls with distance from the money and grows with time to expiry."""
    intrinsic = max(0.0, SPOT - strike) if kind == OPTION_CALL else max(0.0, strike - SPOT)
    years = max((expiry - DAY).days, 1) / 365
    return round(intrinsic + 0.4 * SPOT * 0.12 * math.sqrt(years) * math.exp(-abs(strike - SPOT) / 600), 1) + 1.0


class DriveDown(ConnectionError):
    """What the Drive client raises when Drive cannot be reached."""


class FakeOwnerDrive(RawFileStore):
    """The owner's Drive project folder: write-once files, index files replaced in place; `down` fails every call."""

    name = "fake owner drive"

    def __init__(self):
        self.files: dict[str, bytes] = {}
        self.down = False

    def get(self, path):
        self._reachable()
        return self.files.get(path)

    def put(self, path, data):
        self._reachable()
        if path in self.files and self.files[path] != data:
            raise RawFileConflict(path)
        self.files[path] = data

    def file_id(self, path):
        self._reachable()
        return path if path in self.files else None

    def replace_contents(self, file_id, data):
        self._reachable()
        self.files[file_id] = data

    def _reachable(self):
        if self.down:
            raise DriveDown("drive unreachable (HTTP 503)")


class FakeSlack(AlertSender):
    """#fno-desk: `down` refuses every post, as an unset token or an HTTP error does."""

    def __init__(self):
        self.sent: list[str] = []
        self.down = False

    def send(self, text):
        if self.down:
            raise ConnectionError("slack unreachable")
        self.sent.append(text)
        return "alert sent to #fno-desk"


class FakeClock:
    """The one clock: `fno.models.now_ist` reads it (through `datetime.now`), the run's sleep advances it, and git
    dates every commit by it (`GIT_COMMITTER_DATE`, read by each git call the run starts), so D3's deadline rule sees
    the fixture day's times."""

    def __init__(self, environ, start: datetime = START):
        self.environ = environ
        self.set(start)

    def __call__(self) -> datetime:
        return self.now

    def set(self, moment: datetime) -> None:
        self.now = moment
        stamp = f"{moment.isoformat()}"
        self.environ["GIT_COMMITTER_DATE"] = self.environ["GIT_AUTHOR_DATE"] = stamp

    def advance(self, seconds: float) -> None:
        self.set(self.now + timedelta(seconds=seconds))

    def datetime_class(self):
        clock = self

        class ClockDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return clock.now.astimezone(tz) if tz else clock.now.replace(tzinfo=None)

        return ClockDatetime


class NoNseArchive:
    """NSE's archive library: every file not published (final settlement is asked only for expired legs)."""

    def get(self, path):
        return None


class ScriptedProcess(Process):
    def __init__(self, clock: FakeClock, ends_at: datetime, work, lines: list[str]):
        self.clock, self.ends_at, self.work, self.printed, self.code, self.stopped = (
            clock,
            ends_at,
            work,
            lines,
            None,
            False,
        )

    def poll(self):
        if self.code is None and not self.stopped and self.clock() >= self.ends_at:
            try:
                self.code = self.work()
            except Exception:  # noqa: BLE001 - a crashing command exits 1 with its traceback, as a real child does
                self.printed, self.code = traceback.format_exc().splitlines(), 1
        return self.code

    def lines(self):
        return list(self.printed)

    def stop(self):
        self.stopped = True


class Children(Processes):
    """The child commands: `script[arguments] = (minutes after start, work)`; `work()` does what the real command
    leaves behind and returns its exit code. A command not in the script is a test error, never a silent pass."""

    def __init__(self, clock: FakeClock, script: dict):
        self.clock, self.script, self.started = clock, script, []

    def start(self, arguments) -> Process:
        key = tuple(arguments)
        minutes, work, lines = self.script[key[:2] if key[:2] == ("desk", "book1") else key]
        self.started.append((self.clock(), key))
        return ScriptedProcess(self.clock, self.clock() + timedelta(minutes=minutes), work, lines)


def groww_part(store, day, name: str, at: datetime) -> None:
    """What a Groww quote part leaves: its attempt (the csv to Drive, the sidecar committed) and its canonical."""
    snapshot_id = f"{name}_{at:%Y%m%d_%H%M%S}"
    write_snapshot(store, snapshot_id, market_rows(at), at, at + timedelta(seconds=30), day=day, spot=SPOT)
    store.put(QuoteSnapshotRecorder.path(day, f"{name}_{day:%Y%m%d}.canonical"), snapshot_id.encode())


def nse_part(store, day, at: datetime) -> None:
    """What NSE's part leaves: its whole attempt and the canonical marker, all committed (NSE's chain is public)."""
    snapshot_id = f"nifty_{at:%Y%m%d_%H%M%S}"
    for name, data in ((f"{snapshot_id}.meta.json", b"{}"), (f"nifty_{day:%Y%m%d}.canonical", snapshot_id.encode())):
        store.put(QuoteSnapshotRecorder.path(day, name, NSE_DATASET), data)
