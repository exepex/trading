"""Response 228 point 5 (ChatGPT review 128): an exit that waits keeps its risk. After the short legs close while the
protection still waits, or while a delivered alert has closed nothing, the next morning's real C2 risk book counts the
units still held, and a new entry that would breach a cap misses at its fill. An alert never marks an exit closed."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from fno.books.account import PaperAccount
from fno.desk.exits import ExitDesk
from fno.desk.owner_timing.availability import AlwaysAvailable
from fno.desk.owner_timing.clock import OwnerTimingClock
from fno.desk.owner_timing.due_fill import DueFill
from fno.desk.owner_timing.entry_range import ApprovedLimit
from fno.desk.owner_timing.exit_alerts import AlertThenWait
from fno.desk.owner_timing.exit_fills import OwnerTimingExits
from fno.desk.owner_timing.fill_risk import FillDayRisk
from fno.desk.owner_timing.outcomes import MISSED_RISK_CAP, DueMark
from fno.desk.records import DeskRecords
from fno.desk.status import open_positions
from fno.desk.wiring import open_desk_journal
from fno.research_engine.implied_vol import Black76
from fno.risk.book_view import load_risk_book
from fno.risk.manager import RiskManager
from fno.risk.rules import MaxOpenTrades
from tests.desk.builders import (
    CHARGES,
    DAY,
    LOT,
    at,
    contract,
    enter,
    fly_order,
    fly_proposal,
    fly_rows,
    passed,
    write_snapshot,
)
from tests.desk_owner_timing.fakes import CALENDAR, Due, Marks, MemoryTimingLog, Poster, Settable, ist

BOOK = "book1_rules"
FIRST_MARK = ist(date(2026, 10, 15), 10, 15)
NEXT_MORNING = DueMark(date(2026, 10, 16), ist(date(2026, 10, 16), 10, 15))
NO_PROTECTION = {(25200, "CE"): {"valid": False, "reason": "no trade today"}}
FLY = {contract(25000, "CE"): -LOT, contract(25000, "PE"): -LOT, contract(25200, "CE"): LOT, contract(24800, "PE"): LOT}


class SeenBooks(MaxOpenTrades):
    """C2's own open-trades cap of one, keeping the risk book it was given."""

    def __init__(self):
        super().__init__(1)
        self.books = []

    def check(self, proposal, book, market):
        self.books.append(book)
        return super().check(proposal, book, market)


@pytest.fixture
def opened(root, store, snapshots, entry_desk):
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))
    enter(root, snapshots, entry_desk, fly_order())


def next_entry_miss(root, marks: Marks) -> tuple[str, dict[str, int]]:
    """A second fly due next morning, checked by the real fill-day risk on the account as the waiting exit left it."""
    marks.put(NEXT_MORNING.mark, fly_rows())
    order = fly_order("t2", decided_at=ist(date(2026, 10, 15), 15, 5))
    priced = DueFill(OwnerTimingClock(60, CALENDAR, AlwaysAvailable()), marks, ApprovedLimit(), CHARGES).price(
        order, NEXT_MORNING
    )
    terms = {trade_id: fly_proposal(trade_id).terms for trade_id in ("t1", "t2")}
    rule = SeenBooks()
    books = lambda account, market: load_risk_book(root, account, market, terms)  # noqa: E731
    reason = FillDayRisk(RiskManager([rule], {}), books, 0.065, Black76(), 1e9, CHARGES).miss(order, priced)
    [held] = rule.books[0].open_trades
    return reason, {name: units for name, units in held.units.items() if units}


def test_protection_still_waiting_keeps_the_trade_open_in_next_mornings_risk_book(root, opened, exit_desk):
    marks = Marks()
    exits = OwnerTimingExits(OwnerTimingClock(60, CALENDAR, AlwaysAvailable()), marks, exit_desk, MemoryTimingLog(),
                             "verdict", 60, CHARGES, Settable(FIRST_MARK + timedelta(minutes=5)))  # fmt: skip
    marks.put(FIRST_MARK, fly_rows(NO_PROTECTION))
    with open_desk_journal(BOOK, root) as journal:
        exits.apply(BOOK, open_positions(journal.records)[0], ist(DAY, 15, 20), journal)
    reason, held = next_entry_miss(root, marks)
    assert held == {contract(25200, "CE"): LOT}  # the shorts are bought back; the protection is still held
    assert reason == MISSED_RISK_CAP


def test_a_delivered_alert_closes_nothing_and_the_whole_trade_counts(root, opened, store, snapshots, alerts,
                                                                     settlements, clock):  # fmt: skip
    write_snapshot(store, "later", fly_rows(), at(15, 16), at(15, 16, 40))
    poster = Poster()
    desk = ExitDesk(CHARGES, alerts, settlements, clock, AlertThenWait(poster, MemoryTimingLog()))
    snapshot = snapshots.snapshot(DAY, "later")
    with open_desk_journal(BOOK, root) as journal:
        desk.review(BOOK, snapshot, journal, {"t1": [Due()]}, passed(snapshot))
    assert len(poster.posted) == 1 and open_positions(DeskRecords(PaperAccount(root, BOOK)))
    reason, held = next_entry_miss(root, Marks())
    assert held == FLY and reason == MISSED_RISK_CAP
