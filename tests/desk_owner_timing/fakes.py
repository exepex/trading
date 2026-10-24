"""Shared fakes for the owner-timing tests (story E8): the real NSE calendar, a set of away days, an in-memory seal
log with commit times, the availability file's text, due-mark copies, E8's records in memory and a fixed fill-day
risk answer, a Slack poster and an exit rule that has fired."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from fno.cards.posting import CardPoster, PostReceipt
from fno.config import ROOT
from fno.desk.exit_rules import ExitRule
from fno.desk.owner_timing.availability import Availability, Seal, SealLog
from fno.desk.owner_timing.fill_risk import FillRisk
from fno.desk.owner_timing.mark_levels import MarkSnapshot
from fno.desk.owner_timing.mark_snapshots import MarkSnapshots
from fno.desk.owner_timing.timing_log import TimingLog, TimingRecord
from fno.desk.snapshot import RecordedExecutionSnapshots
from fno.models import IST
from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.research_data.calendar import load_session_calendar
from fno.research_data.panel_reader import FutureQuote
from tests.desk.builders import EXPIRY, DictStore, write_snapshot

CALENDAR = load_session_calendar(ROOT / "research" / "data" / "calendar" / "nse_sessions.csv")
SALT = "salt," + "ab" * 16
NEAR_FUTURE = FutureQuote(EXPIRY, 25000.0, 0.0, 1, 0)
SLACK_TS = "1792058160.000100"  # 15 Oct 2026, a Slack message timestamp


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


class Marks(MarkSnapshots):
    """A4-format copies at chosen marks (`write_snapshot`'s files), each read back as a due mark's copy."""

    def __init__(self, spot: float | None = 25000.0, futures=(NEAR_FUTURE,)):
        self.store, self.spot, self.futures, self.read = DictStore(), spot, tuple(futures), []

    def put(self, mark: datetime, rows: list[dict], name: str | None = None) -> str:
        name = name or f"a16_{mark:%Y%m%d_%H%M}"
        write_snapshot(self.store, name, rows, mark, mark + timedelta(seconds=50), day=mark.date())
        return name

    def at(self, day: date, mark: datetime) -> MarkSnapshot | None:
        self.read.append(mark)
        name = f"a16_{mark:%Y%m%d_%H%M}"
        if QuoteSnapshotRecorder.path(day, f"{name}.csv") not in self.store.files:
            return None
        prices = RecordedExecutionSnapshots(self.store).snapshot(day, name)
        return MarkSnapshot(prices, self.spot, self.futures)


class MemoryTimingLog(TimingLog):
    def __init__(self):
        self.alerts: dict = {}
        self.records: list[TimingRecord] = []

    def alert_time(self, account, trade_id):
        return self.alerts.get((account, trade_id))

    def alerted(self, account, trade_id, delivered_at):
        self.alerts.setdefault((account, trade_id), delivered_at)

    def record(self, record):
        self.records.append(record)


class FixedRisk(FillRisk):
    def __init__(self, miss: str = ""):
        self.miss_reason, self.asked = miss, []

    def miss(self, order, priced):
        self.asked.append(order.proposal.trade_id)
        return self.miss_reason


class Settable:
    def __init__(self, moment: datetime):
        self.now = moment

    def __call__(self) -> datetime:
        return self.now


class Poster(CardPoster):
    def __init__(self, ts: str | None = SLACK_TS):
        self.ts, self.posted = ts, []

    def post(self, text):
        self.posted.append(text)
        return PostReceipt("posted" if self.ts else "not sent: fixture", self.ts)


class Due(ExitRule):
    name = "fixture"

    def reached(self, position, context):
        return "time stop: fixture"
