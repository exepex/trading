"""Fakes for the 15-minute recorder's tests (story A16): clock, source, alerts, publisher, servers, calendar."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from fno.alerts.sender import NOT_SENT, SENT, AlertSender
from fno.intraday.clock import ClockCheck
from fno.intraday.document import CallRecord, SnapshotDocument
from fno.intraday.heartbeat import Heartbeat
from fno.intraday.ledger import SlotLedger
from fno.intraday.realised_vol import QuoteSnapshotRv15m
from fno.intraday.recorder import IntradayRecorder
from fno.intraday.rv_table import RvTable
from fno.intraday.session_rv import SessionRv
from fno.intraday.snapshot_files import SnapshotFiles
from fno.intraday.source import IntradayQuoteSource
from fno.intraday.sync import LedgerSync
from fno.models import IST
from fno.research_data.calendar import CsvSessionCalendar
from fno.server_clock import ServerClock, ServerTimeUnknown
from fno.storage.raw_store import AreaStore, LocalFolderStore

SOURCE_LINK = "https://example.org/circular.pdf"
CALENDAR = "\n".join([
    "date,kind,description,source_url",
    f"2026-10-17,special,special Saturday session,{SOURCE_LINK}",
    f"2026-10-20,holiday,Dussehra,{SOURCE_LINK}",
    f"2026-11-08,muhurat,Diwali muhurat,{SOURCE_LINK}",
])  # fmt: skip
DAY = date(2026, 10, 15)  # a regular Thursday


def ist(day: date, hour: int, minute: int, second: float = 0) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=IST) + timedelta(seconds=second)


class FakeClock:
    def __init__(self, start: datetime):
        self.moment = start

    def now(self) -> datetime:
        return self.moment

    def sleep(self, seconds: float) -> None:
        self.moment += timedelta(seconds=seconds)

    def advance(self, seconds: float) -> None:
        self.moment += timedelta(seconds=seconds)


def level_at(mark: datetime) -> float:
    """A deterministic index path: up 0.1% each mark, from 25,000 at 09:15 (day-dependent start)."""
    k = (mark.hour * 60 + mark.minute - (9 * 60 + 15)) // 15
    return round(25000 * (1 + 0.001 * k) + mark.day, 2)


class FakeSource(IntradayQuoteSource):
    """Answers in `latency` seconds with a fresh index level; `plans` maps a mark's HH:MM to a change of behaviour:
    "fail" (index call fails), "old" (source time 121 s old), "repeat" (previous mark's level), "partial" (one
    contract missing), "slow" (index answered 121 s after the mark)."""

    name = "fakegroww"

    def __init__(self, clock: FakeClock, plans: dict | None = None, latency: float = 1.0, contracts: int = 4):
        self.clock, self.plans, self.latency, self.contracts = clock, plans or {}, latency, contracts
        self.prepared: list[date] = []
        self.taken: list[datetime] = []

    def prepare(self, session: date) -> None:
        self.prepared.append(session)

    def take(self, session: date, mark: datetime) -> SnapshotDocument:
        plan = self.plans.get(f"{mark:%H:%M}", "")
        self.taken.append(mark)
        sent = self.clock.now()
        self.clock.advance(121 if plan == "slow" else self.latency)
        received = self.clock.now()
        level = level_at(mark - timedelta(minutes=15)) if plan == "repeat" else level_at(mark)
        index = CallRecord("index", sent, None if plan == "fail" else received, None if plan == "fail" else
                           {"last_price": level}, "GrowwAPIException" if plan == "fail" else "")  # fmt: skip
        source_time = received - timedelta(seconds=121 if plan == "old" else 1)
        quotes = [CallRecord(f"quote {i}", received, received, {"bid_price": 1, "offer_price": 2}, "", {})
                  for i in range(self.contracts - (1 if plan == "partial" else 0))]  # fmt: skip
        chains = [CallRecord(f"chain {n}", received, received, {"strikes": {}}, "", {"contracts": self.contracts // 2})
                  for n in (1, 2)]  # fmt: skip
        doc = SnapshotDocument(
            self.name, "NIFTY", session, mark, index, None if plan == "fail" else level,
            None if plan == "fail" else source_time, chains=chains, quotes=quotes, expected_contracts=self.contracts,
            two_sided_contracts=len(quotes), failures=["index"] if plan == "fail" else [],
        )  # fmt: skip
        doc.index_basis = "" if plan == "fail" else "quote_last_trade_time"
        doc.finished_at = self.clock.now()
        return doc


class FakeAlerts(AlertSender):
    """Records every text; answers "sent" unless `failing` (then as with no Slack token)."""

    def __init__(self, failing: bool = False):
        self.sent: list[str] = []
        self.failing = failing

    def send(self, text: str) -> str:
        self.sent.append(text)
        return NOT_SENT.format(reason="test") if self.failing else SENT


class FakePublisher(LedgerSync):
    def __init__(self):
        self.commits: list[str] = []
        self.pulls = 0

    def pull(self) -> str:
        self.pulls += 1
        return "pulled (fake)"

    def commit(self, what: str) -> str:
        self.commits.append(what)
        return f"committed {what}"


class FixedServer(ServerClock):
    """A server whose clock is `offset` seconds ahead of the host's (None: it gives no trusted time)."""

    def __init__(self, name: str, offset: float | None, host_now):
        self.name, self.offset, self.host_now = name, offset, host_now

    def now(self) -> datetime:
        if self.offset is None:
            raise ServerTimeUnknown(f"HTTP 400 from {self.name}, a Date header: an error answer's time is not trusted")
        return self.host_now() + timedelta(seconds=self.offset)


def calendar() -> CsvSessionCalendar:
    return CsvSessionCalendar(CALENDAR)


def build(tmp_path, clock: FakeClock, plans: dict | None = None, skew: float | None = 0.4, drive=None):
    """A recorder on local folders with every fake; returns (recorder, source, alerts, publisher, files)."""
    store = AreaStore(drive or LocalFolderStore(tmp_path / "drive"), "raw")
    source, alerts, publisher = FakeSource(clock, plans), FakeAlerts(), FakePublisher()
    ledger = SlotLedger(tmp_path)
    files = SnapshotFiles(source.name, store, ledger)
    session_rv = SessionRv(files, calendar(), RvTable(tmp_path), QuoteSnapshotRv15m(), clock.now)
    clocks = ClockCheck([FixedServer("github", skew, clock.now), FixedServer("slack", skew, clock.now)], clock.now)
    recorder = IntradayRecorder(source, files, ledger, Heartbeat(tmp_path), calendar(), alerts, clocks, session_rv,
                                publisher, clock.now, clock.sleep)  # fmt: skip
    return recorder, source, alerts, publisher, files
