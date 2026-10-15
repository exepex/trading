"""Story E4c: the entry check before any leg fills (criteria 1-5, 11). The short iron fly of `builders.py`, 65 units:
protective legs 25200 CE and 24800 PE (bought), short legs 25000 CE and 25000 PE (sold)."""

import csv

import pytest

from fno.books.account import PaperAccount
from fno.constants import (
    BOOK1_RULES,
    OPTION_CALL,
    OPTION_PUT,
    OUTCOME_NOT_OPENED,
    OUTCOME_OPENED,
    OUTCOME_REFUSED,
    PROTECTION_NOT_BUYABLE,
    PROTECTION_NOT_SELLABLE,
    SHORT_LEG_NOT_SELLABLE,
    STRUCTURE_CALL_CREDIT_SPREAD,
    STRUCTURE_LONG_CALL,
    STRUCTURE_LONG_PUT,
    STRUCTURE_PUT_CREDIT_SPREAD,
)
from fno.desk.entries import EntryOrder
from fno.desk.entry_check import entry_problems
from fno.desk.records import DeskRecords
from fno.research_engine.structures import BOUGHT, SOLD
from fno.risk.book_view import load_risk_book
from fno.risk.inputs import Proposal, TradeTerms

from .builders import (
    DAY,
    EXPIRY,
    FLY_QUOTES,
    approved,
    at,
    contract,
    decision_market,
    enter,
    fly_order,
    fly_proposal,
    fly_rows,
    write_snapshot,
)

CE, PE = OPTION_CALL, OPTION_PUT
WING, SHORT = (25200, CE), (25000, PE)


def entered(root, store, snapshots, entry_desk, changes, order=None, snapshot_id="exec"):
    write_snapshot(store, snapshot_id, fly_rows(changes), at(15, 15), at(15, 15, 40))
    return enter(root, snapshots, entry_desk, order or fly_order(), snapshot_id)


def refused_with(code, strike_kind):
    return f"{code} ({contract(*strike_kind)}, 65 units)"


def nothing_written(root):
    account = PaperAccount(root, BOOK1_RULES)
    return account.fills() == [] and DeskRecords(account).fill_rows() == [] and len(account.ledger_rows()) == 1


@pytest.mark.parametrize(
    "side, changes, code",
    [
        ("protective bid", lambda n: {WING: {"bid_qty": n}}, PROTECTION_NOT_SELLABLE),
        ("protective ask", lambda n: {WING: {"size": n, "bid_qty": 1000}}, PROTECTION_NOT_BUYABLE),
        ("short bid", lambda n: {SHORT: {"bid_qty": n}}, SHORT_LEG_NOT_SELLABLE),
    ],
)
@pytest.mark.parametrize("size, opens", [(64, False), (65, True), (66, True)])
def test_a_size_equal_to_the_units_passes_one_less_is_refused_before_any_fill(
    root, store, snapshots, entry_desk, side, changes, code, size, opens
):
    """Criteria 1-2: units - 1 refuses with the side's code and writes nothing; units and units + 1 open."""
    result = entered(root, store, snapshots, entry_desk, changes(size))
    if opens:
        assert result.outcome == OUTCOME_OPENED
        return
    leg = WING if side.startswith("protective") else SHORT
    assert (result.outcome, result.reason) == (OUTCOME_NOT_OPENED, refused_with(code, leg))
    assert result.legging_cost_rs is None and nothing_written(root)


@pytest.mark.parametrize(
    "change",
    [
        None,  # no quote at all
        {"bid": None},  # no bid: A4 makes the quote unusable both ways
        {"bid": 0},
        {"bid_qty": 0},
        {"bid": 72, "ask": 71},  # crossed
        {"valid": False, "reason": "no trade today"},
    ],
    ids=["no quote", "no bid", "bid 0", "no bid size", "crossed", "no trade today"],
)
def test_a_protective_leg_a4_cannot_use_is_not_buyable_and_nothing_is_bought(
    root, store, snapshots, entry_desk, change
):
    """Criterion 3, the first protective leg; the second protective leg in `test_entries.py`."""
    result = entered(root, store, snapshots, entry_desk, {WING: change})
    assert (result.outcome, result.reason) == (OUTCOME_NOT_OPENED, refused_with(PROTECTION_NOT_BUYABLE, WING))
    assert nothing_written(root)


def test_a_case_failing_two_checks_records_the_first_in_the_fixed_order(root, store, snapshots, entry_desk):
    """Criterion 4: the second wing not buyable and the first wing not sellable: the legs in E4's order, for each its
    opening side then its closing side, so the first wing's closing side is recorded."""
    changes = {WING: {"bid_qty": 1}, (24800, PE): None, SHORT: {"valid": False}}
    result = entered(root, store, snapshots, entry_desk, changes)
    assert result.reason == refused_with(PROTECTION_NOT_SELLABLE, WING)
    snapshot = snapshots.snapshot(DAY, "exec")
    assert entry_problems(snapshot, fly_order().legs(), 65) == [
        refused_with(PROTECTION_NOT_SELLABLE, WING),
        refused_with(PROTECTION_NOT_BUYABLE, (24800, PE)),
        refused_with(SHORT_LEG_NOT_SELLABLE, SHORT),
    ]


def test_the_refusals_before_the_entry_check_come_first_and_a_rerun_returns_the_record(
    root, store, snapshots, entry_desk
):
    """Criterion 4: E4's refusals (here C2's decision for another day) come before the check; a rerun of a refused
    entry returns the recorded outcome."""
    other_day = fly_order(risk=approved(fly_proposal(), day=DAY.replace(day=13)))
    assert entered(root, store, snapshots, entry_desk, {WING: {"bid_qty": 1}}, other_day).outcome == OUTCOME_REFUSED
    first = entered(root, store, snapshots, entry_desk, {WING: {"bid_qty": 1}}, fly_order("t2"))
    again = enter(root, snapshots, entry_desk, fly_order("t2"))
    assert first == again and first.reason == refused_with(PROTECTION_NOT_SELLABLE, WING)


def test_the_event_row_holds_no_quote_figure(root, store, snapshots, entry_desk):
    """Criterion 5: the committed row names the contract and the units, never a bid, ask or size of the snapshot."""
    entered(root, store, snapshots, entry_desk, {WING: {"bid_qty": 64}})
    (events,) = root.rglob("desk_events.csv")
    (row,) = csv.DictReader(events.open())
    figures = {f"{v:g}" for quote in FLY_QUOTES.values() for v in quote} | {"64", "1000"}
    assert row["reason"] == refused_with(PROTECTION_NOT_SELLABLE, WING)
    assert not [f for f in figures if f in row["reason"].replace(contract(*WING), "").replace("65 units", "")]


def str1_order(code, width, legs, trade_id="t1"):
    """An approved order for one of STR1's structures, on the fly's strikes (65 units, one lot)."""
    base = fly_proposal(trade_id, legs=legs)
    proposal = Proposal(base.trade_id, TradeTerms(code, width, 1), base.lot_size, base.legs)
    order = fly_order(trade_id)
    return EntryOrder(order.book, order.strategy, order.decision_id, order.decided_at, proposal, EXPIRY,
                      approved(proposal))  # fmt: skip


STR1_CASES = {
    "LC": (STRUCTURE_LONG_CALL, 0, ((25200, CE, BOUGHT),), WING, PROTECTION_NOT_SELLABLE),
    "LP": (STRUCTURE_LONG_PUT, 0, ((24800, PE, BOUGHT),), (24800, PE), PROTECTION_NOT_SELLABLE),
    "CCS, its wing": (STRUCTURE_CALL_CREDIT_SPREAD, 200, ((25000, CE, SOLD), (25200, CE, BOUGHT)), WING,
                      PROTECTION_NOT_SELLABLE),
    "PCS, its short": (STRUCTURE_PUT_CREDIT_SPREAD, 200, ((25000, PE, SOLD), (24800, PE, BOUGHT)), SHORT,
                       SHORT_LEG_NOT_SELLABLE),
}  # fmt: skip


@pytest.mark.parametrize("code, width, legs, thin, refused", STR1_CASES.values(), ids=STR1_CASES.keys())
def test_str1_structures_one_leg_or_vertical_are_checked_the_same(
    root, store, snapshots, entry_desk, code, width, legs, thin, refused
):
    """Criterion 2: a one-leg bought option (LC, LP) and a vertical; one leg below the units on its checked side refuses
    the whole structure, nothing bought; with every size covering, it opens."""
    order = str1_order(code, width, legs)
    result = entered(root, store, snapshots, entry_desk, {thin: {"bid_qty": 64}}, order)
    assert (result.outcome, result.reason) == (OUTCOME_NOT_OPENED, refused_with(refused, thin))
    assert nothing_written(root)
    covered = entered(root, store, snapshots, entry_desk, {}, str1_order(code, width, legs, "t2"), "ok")
    assert covered.outcome == OUTCOME_OPENED


def test_the_check_depends_only_on_the_snapshot_it_is_given(store, snapshots):
    """Criterion 11 (the E8 hook): one order, two snapshots of the day, two answers."""
    write_snapshot(store, "first", fly_rows({WING: {"bid_qty": 64}}), at(15, 15), at(15, 15, 40))
    write_snapshot(store, "later", fly_rows(), at(15, 45), at(15, 45, 40))
    legs = fly_order().legs()
    assert entry_problems(snapshots.snapshot(DAY, "first"), legs, 65) == [refused_with(PROTECTION_NOT_SELLABLE, WING)]
    assert entry_problems(snapshots.snapshot(DAY, "later"), legs, 65) == []


def test_a_refused_entry_is_not_new_risk_of_the_session(root, store, snapshots, entry_desk):
    """Criterion 10 (C5 merged): no E1 ledger row, so C2's `session_trades` for the day is empty."""
    entered(root, store, snapshots, entry_desk, {WING: {"bid_qty": 64}})
    assert load_risk_book(root, BOOK1_RULES, decision_market(), {}).session_trades == ()
