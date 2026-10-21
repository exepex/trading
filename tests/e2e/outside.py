"""Story O2: the fakes of the daily run's outside services, and only those: the owner's Drive, Slack, Groww's market
data, NSE's archive, the clock, and the child commands (NIFTY's 3 pm part and the 15:15 capture run A4's real recorder
over the fake Groww; Book 1's decision runs the real Book 1). Every one has a switch for its family's failure."""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta

from fno.alerts.sender import NOT_SENT, SENT, AlertSender
from fno.constants import OPTION_CALL, OPTION_PUT
from fno.models import IST, OptionChain, OptionQuote, QuoteBook
from fno.storage.raw_store import RawFileConflict, RawFileStore
from tests.desk.builders import LOT, fly_rows

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


class Groww:
    """Groww itself, shared by every recorder of the day: `down` fails every call, as a Groww outage does."""

    def __init__(self):
        self.down = False


class FixtureProvider:
    """Groww's market data for the fixture day, as one recorder sees it on its own clock: NIFTY at `SPOT`, five
    expiries, a smooth chain 600 points either side. Read-only, as the real adapter: there is no order call."""

    name = "groww"
    EXPIRIES = (date(2026, 10, 20), date(2026, 10, 27), date(2026, 11, 3), date(2026, 11, 24), date(2026, 12, 29))

    def __init__(self, groww: Groww, clock: FakeClock):
        self.groww, self.clock = groww, clock

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
        if self.groww.down:
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
        self.down_areas: set[str] = set()  # e.g. {"raw"}: only those areas fail

    def get(self, path):
        self._reachable(path)
        return self.files.get(path)

    def put(self, path, data):
        self._reachable(path)
        if path in self.files and self.files[path] != data:
            raise RawFileConflict(path)
        self.files[path] = data

    def file_id(self, path):
        self._reachable(path)
        return path if path in self.files else None

    def replace_contents(self, file_id, data):
        self._reachable(file_id)
        self.files[file_id] = data

    def _reachable(self, path: str):
        if self.down or path.split("/", 1)[0] in self.down_areas:
            raise DriveDown("drive unreachable (HTTP 503)")


class FakeSlack(AlertSender):
    """#fno-desk: `down` refuses every post, as an unset token or an HTTP error does; the outcome line is the real
    sender's (`SENT`, or `NOT_SENT` with the reason)."""

    def __init__(self):
        self.sent: list[str] = []
        self.refused: list[str] = []
        self.down = False

    def send(self, text):
        if self.down:
            self.refused.append(text)
            return NOT_SENT.format(reason="ConnectionError")
        self.sent.append(text)
        return SENT


class Killed(BaseException):
    """The routine's container dies: no step's handler sees it (they catch `Exception`), so the run just ends."""


class FakeClock:
    """The one clock: `fno.models.now_ist` reads it (through `datetime.now`), the run's sleep advances it, and git
    dates every commit by it (`GIT_COMMITTER_DATE`, read by each git call the run starts), so D3's deadline rule sees
    the fixture day's times."""

    def __init__(self, environ, start: datetime = START):
        self.environ = environ
        self.set(start)

    kill_when = None  # a condition: once true, the next reading of the clock kills the run
    on_condition = ()  # (condition, action) pairs in turn: once the first is true, a reading runs its action once

    def __call__(self) -> datetime:
        if self.kill_when is not None and self.kill_when():
            self.kill_when = None
            raise Killed(f"killed at {self.now:%H:%M:%S}")
        if self.on_condition and self.on_condition[0][0]():
            (_, action), *self.on_condition = self.on_condition
            action()
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
                moment = clock()  # every reading of the run's time can kill the run (`kill_when`)
                return moment.astimezone(tz) if tz else moment.replace(tzinfo=None)

        return ClockDatetime


class NoNseArchive:
    """NSE's archive library: every file not published (final settlement is asked only for expired legs)."""

    def get(self, path):
        return None
