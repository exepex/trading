"""E8 rule 6 and judge 203 conditions 1, 3 and 4: C2's rules run again at the fill on the due mark's copy and the
verdict account after the morning's earlier fills; a funds failure is "missed, insufficient funds", any other failure
or C4's maximum loss over the cap is "missed, over risk cap", and a value missing from the copy
is "missed, no quote"."""

from __future__ import annotations

from datetime import date

import pytest

from fno.books.account import PaperAccount
from fno.desk.owner_timing.availability import AlwaysAvailable
from fno.desk.owner_timing.clock import OwnerTimingClock
from fno.desk.owner_timing.due_fill import DueFill
from fno.desk.owner_timing.entry_range import ApprovedLimit
from fno.desk.owner_timing.fill_risk import FillDayRisk
from fno.desk.owner_timing.outcomes import MISSED_FUNDS, MISSED_NO_FUTURE, MISSED_NO_QUOTE, MISSED_RISK_CAP, DueMark
from fno.research_engine.implied_vol import Black76
from fno.risk.book_view import load_risk_book
from fno.risk.manager import RiskManager
from fno.risk.margins import StressedMargin
from fno.risk.rules import MarginRoom
from fno.risk.trade_costs import SimulatorTradeCosts
from fno.risk.verdict import RiskRule
from tests.desk.builders import CHARGES, DAY, at, enter, fly_order, fly_proposal, fly_rows, write_snapshot
from tests.desk_owner_timing.fakes import CALENDAR, Marks, ist

FILL_DAY = date(2026, 10, 15)
DUE = DueMark(FILL_DAY, ist(FILL_DAY, 10, 15))
NO_CAP = 1e9


class Fixed(RiskRule):
    def __init__(self, name: str, ok: bool):
        self.name, self.ok, self.books = name, ok, []

    def check(self, proposal, book, market):
        self.books.append(book)
        return self.verdict(self.ok, "fixture")


class FlatMargin(StressedMargin):
    method = "fixture"

    def __init__(self, rupees: float):
        self.rupees = rupees

    def margin(self, terms, day):
        return self.rupees

    def margin_at_entry(self, terms, day):
        return self.rupees

    def broker_margin(self, terms, day):
        return self.rupees

    def record(self, day=None):
        return {}


def priced(marks=None, order=None):
    marks = marks or Marks()
    marks.put(DUE.mark, fly_rows())
    clock = OwnerTimingClock(60, CALENDAR, AlwaysAvailable())
    return DueFill(clock, marks, ApprovedLimit(), CHARGES).price(order or fly_order(), DUE)


def risk(root, *rules, max_loss=NO_CAP):
    books = lambda account, market: load_risk_book(root, account, market, {"t1": fly_proposal().terms})  # noqa: E731
    return FillDayRisk(RiskManager(rules, {}), books, 0.065, Black76(), max_loss, CHARGES)


def test_every_rule_passing_fills(root):
    assert risk(root, Fixed("margin_room", True), Fixed("open_trades", True)).miss(fly_order(), priced()) == ""


@pytest.mark.parametrize(("failing", "reason"), [("margin_room", MISSED_FUNDS), ("open_trades", MISSED_RISK_CAP)])
def test_a_failed_rule_misses_with_its_reason(root, failing, reason):
    rules = [Fixed(name, name != failing) for name in ("margin_room", "open_trades")]
    assert risk(root, *rules).miss(fly_order(), priced()) == reason


def test_the_maximum_loss_on_the_fill_prices_over_the_cap_misses(root):
    assert risk(root, Fixed("open_trades", True), max_loss=1.0).miss(fly_order(), priced()) == MISSED_RISK_CAP


@pytest.mark.parametrize(
    ("marks", "reason"),
    [(Marks(spot=None), MISSED_NO_QUOTE), (Marks(futures=()), MISSED_NO_FUTURE)],
    ids=["no spot", "no future for the expiry"],
)
def test_a_level_missing_from_the_copy_misses_with_its_reason(root, marks, reason):
    assert risk(root, Fixed("open_trades", True)).miss(fly_order(), priced(marks)) == reason


def test_the_check_reads_the_account_after_the_mornings_earlier_fills(root, store, snapshots, entry_desk):
    rule = Fixed("open_trades", True)
    risk(root, rule).miss(fly_order("t2"), priced(order=fly_order("t2")))
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))
    enter(root, snapshots, entry_desk, fly_order())
    risk(root, rule).miss(fly_order("t2"), priced(order=fly_order("t2")))
    assert [len(b.open_trades) for b in rule.books] == [0, 1]


def test_c2s_own_margin_rule_counts_an_earlier_fill(root, store, snapshots, entry_desk):
    order = fly_order("t2")
    cash = PaperAccount(root, "book1_rules").state({}).cash
    room = MarginRoom(FlatMargin(cash * 0.6), SimulatorTradeCosts(CHARGES))
    assert risk(root, room).miss(order, priced(order=order)) == ""
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40), day=DAY)
    enter(root, snapshots, entry_desk, fly_order())
    assert risk(root, room).miss(order, priced(order=order)) == MISSED_FUNDS
