"""A `SchoolFleet` over a's fakes (story MS-P1j's unit tests): two sessions, BANKNIFTY open, the other roads closed."""

from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from pathlib import Path

from fno.school.constants import ClosureReason, RoadCode
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.roads import OPEN, ROADS, RoadStatus
from fno.school.fakes import (
    FakeAccounts,
    FakeDashcam,
    FakeFills,
    FakeRoadCatalogue,
    FakeSettlementSource,
    FakeSnapshotSource,
)
from fno.school.fleet.books import Books
from fno.school.fleet.counts_file import SessionCounts
from fno.school.fleet.entry_mids import DashcamEntryMids
from fno.school.fleet.runner import SchoolFleet
from fno.school.safety.law_set import SafetyLaws
from fno.school.settings import school_settings
from fno.school.tickets.book import TicketBook, TicketLedger
from tests.school.contracts import builders as b
from tests.school.contracts.test_settings import GOOD

DAY2 = b.SESSION + timedelta(days=1)
CLOSED = RoadStatus(ClosureReason.CAPTURE_MISSING, "no canonical marker")
OPEN_ROAD = RoadCode.BANKNIFTY_MONTHLY


def all_roads(code: str):
    """A card that drives every road, so one test sees every road scheduled for it."""
    return replace(b.card(code), roads=tuple(r.code for r in ROADS))


class OpenGate:
    def check(self, road_day, snapshot):
        return OPEN


class NoHistory:
    def spots(self, road, session):
        return ()


def days(session: date, open_roads=(OPEN_ROAD,)) -> tuple:
    return tuple(replace(b.road_day(r.code), session=session) if r.code in open_roads
                 else replace(b.road_day(r.code, CLOSED), session=session) for r in ROADS)  # fmt: skip


@dataclass
class Rig:
    root: Path
    drivers: tuple
    laws: tuple = ()
    enabled: bool = True
    snapshots: dict = field(default_factory=dict)
    settlements: dict = field(default_factory=dict)
    seconds: float = 5.0
    open_roads: tuple = (OPEN_ROAD,)
    max_new: int = 5

    def __post_init__(self):
        self.accounts, self.ticket_accounts = FakeAccounts(2_000_000), FakeAccounts(0)
        self.dashcam = FakeDashcam()
        fills = FakeFills(FakeSettlementSource(self.settlements))
        self.snapshots = self.snapshots or {(road, s): replace(b.snapshot(road), session=s)
                                            for road in self.open_roads for s in (b.SESSION, DAY2)}  # fmt: skip
        tickets = TicketBook(fills, TicketLedger(self.ticket_accounts))
        books = Books(self.accounts, self.accounts, tickets, self.ticket_accounts, fills)
        block = {**GOOD, "enabled": self.enabled, "max_new_trades_per_slot": self.max_new}
        catalogue = FakeRoadCatalogue({s: days(s, self.open_roads) for s in (b.SESSION, DAY2)})
        self.fleet = SchoolFleet(
            school_settings({"school": block}), catalogue, FakeSnapshotSource(self.snapshots),
            OpenGate(), NoHistory(), self.drivers, lambda marks: SafetyLaws(self.laws), books, self.dashcam,
            SessionCounts(self.root, None), lambda session: None, DashcamEntryMids(self.dashcam), self.clock(b.SESSION),
            self.seconds,
        )  # fmt: skip

    @staticmethod
    def clock(session: date) -> FixedClock:
        return FixedClock(b.SLOT_AT.replace(year=session.year, month=session.month, day=session.day)
                          + timedelta(minutes=4))  # fmt: skip

    def at(self, session: date) -> "Rig":
        self.fleet.clock = self.clock(session)
        return self
