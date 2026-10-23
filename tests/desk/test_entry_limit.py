"""Story E4, entry limit (orchestrator, 14 Oct 2026): a trade opens only when its net entry at the execution snapshot's
touch is no worse than the entry C2 approved (decision mids, B2's Rs 1 pad, entry charges); otherwise nothing fills,
with the fixed reason `entry_worse_than_approved` and no figure from the snapshot (decision 45, story E2b)."""

import re
from dataclasses import replace
from datetime import date

import pytest

from fno.books.account import PaperAccount
from fno.config import load_app_config
from fno.constants import (
    BOOK1_RULES,
    ENTRY_WORSE_THAN_APPROVED,
    OPTION_CALL,
    OUTCOME_NOT_OPENED,
    OUTCOME_OPENED,
    OUTCOME_REFUSED,
    SIDE_BUY,
    STRUCTURE_LONG_CALL,
)
from fno.costs import order_charges
from fno.desk.entries import WORSE_THAN_APPROVED, EntryOrder
from fno.desk.records import EVENT_COLUMNS, DeskRecords
from fno.research_engine.structures import BOUGHT
from fno.risk.book_view import load_risk_book
from fno.risk.inputs import TradeTerms
from fno.risk.margins import MARGIN_COLUMNS
from fno.risk.wiring import build_risk_manager
from tests.margin_tables import local_tables
from tests.stress_factor_files import factor_file

from .builders import (
    CHARGES,
    DECIDED_AT,
    EXPIRY,
    FLY_LEGS,
    FLY_QUOTES,
    LOT,
    approved,
    approved_entry,
    at,
    decision_market,
    enter,
    fly_order,
    fly_proposal,
    fly_rows,
    row,
    write_snapshot,
)

MIDS = {key: (bid + ask) / 2 for key, (bid, ask) in FLY_QUOTES.items()}


def quotes_with_half_spread(half: float) -> dict:
    return {key: (mid - half, mid + half) for key, mid in MIDS.items()}


def snapshot_with_half_spread(store, half):
    changes = {key: {"bid": bid, "ask": ask} for key, (bid, ask) in quotes_with_half_spread(half).items()}
    write_snapshot(store, "exec", fly_rows(changes), at(15, 15), at(15, 15, 40))


def net_at_touch(half: float, lots: int = 1) -> float:
    """Hand computation: sell at mid - half, buy at mid + half, minus C1's charges on each fill."""
    units, net = LOT * lots, 0.0
    for strike, kind, side in FLY_LEGS:
        buying = side == BOUGHT
        price = MIDS[(strike, kind)] + (half if buying else -half)
        net += (-price if buying else price) * units
        net -= order_charges(price, units, SIDE_BUY if buying else "sell", CHARGES)
    return net


IDS = ("event_id", "day", "book", "strategy", "trade_id", "decision_id", "snapshot_id", "snapshot_sha256")  # names


def assert_no_quote_figure(root, result):
    """Decision 45: the reason is the fixed text and the public row has no shortfall column and no other figure."""
    assert result.outcome == OUTCOME_NOT_OPENED and result.reason == WORSE_THAN_APPROVED
    assert not re.search(r"\d", result.reason)
    [event] = DeskRecords(PaperAccount(root, BOOK1_RULES)).event_rows(result.trade_id)
    assert tuple(event) == EVENT_COLUMNS and "shortfall_rs" not in event
    assert all(not re.search(r"\d", value) for name, value in event.items() if name not in IDS), event
    assert PaperAccount(root, BOOK1_RULES).fills() == []


def test_a_rs_2_wider_half_spread_on_all_four_legs_fills_nothing_and_publishes_no_figure(root, store, snapshots,
                                                                                         entry_desk):  # fmt: skip
    snapshot_with_half_spread(store, 1.0 + 2.0)  # C2 assumed Rs 1 each way; the market charges Rs 3
    result = enter(root, snapshots, entry_desk, fly_order())
    assert approved_entry(fly_proposal()) == pytest.approx(net_at_touch(1.0))  # C2's entry: the touch at Rs 1 half
    assert result.reason.startswith(ENTRY_WORSE_THAN_APPROVED)
    assert_no_quote_figure(root, result)


def test_a_single_leg_long_call_worse_than_approved_publishes_no_figure(root, store, snapshots, entry_desk):
    """For LC or LP the net at the touch is one contract's ask (decision 45): neither it nor the shortfall is kept."""
    legs = ((25200, OPTION_CALL, BOUGHT),)
    quotes = {(25200, OPTION_CALL): (70.0, 71.0)}
    proposal = replace(fly_proposal(legs=legs), terms=TradeTerms(STRUCTURE_LONG_CALL, 0, 1))
    order = EntryOrder(BOOK1_RULES, "fixture-lc-v1", "d-t1", DECIDED_AT, proposal, EXPIRY,
                       approved(proposal, entry_cash=approved_entry(proposal, quotes)))  # fmt: skip
    write_snapshot(store, "exec", [row(25200, OPTION_CALL, 69.0, 73.5)], at(15, 15), at(15, 15, 40))
    assert_no_quote_figure(root, enter(root, snapshots, entry_desk, order))


@pytest.mark.parametrize("half", [1.0, 0.5, 0.05])
def test_an_entry_equal_to_or_better_than_the_approved_one_fills(root, store, snapshots, entry_desk, half):
    snapshot_with_half_spread(store, half)
    result = enter(root, snapshots, entry_desk, fly_order())
    assert result.outcome == OUTCOME_OPENED
    assert PaperAccount(root, BOOK1_RULES).summary()["cash_rs"] == pytest.approx(2_000_000 + net_at_touch(half))


def test_a_paisa_worse_than_approved_fills_nothing(root, store, snapshots, entry_desk):
    snapshot_with_half_spread(store, 1.0)
    result = enter(root, snapshots, entry_desk, fly_order(limit=approved_entry(fly_proposal()) + 0.01))
    assert result.outcome == OUTCOME_NOT_OPENED and result.reason == WORSE_THAN_APPROVED


def test_the_limit_scales_with_the_lots(root, store, snapshots, entry_desk):
    """At a Rs 3 half-spread 2 lots are refused by their 2-lot limit, though their credit beats 1 lot's limit (a limit
    that did not scale would fill them); at the Rs 1 half-spread C2 modelled they fill."""
    snapshot_with_half_spread(store, 3.0)
    order = fly_order("t2", lots=2)
    assert order.risk.entry_cash_rs == pytest.approx(approved_entry(fly_proposal(lots=2)))
    assert net_at_touch(3.0, 2) > approved_entry(fly_proposal(lots=1))
    assert enter(root, snapshots, entry_desk, order).outcome == OUTCOME_NOT_OPENED
    snapshot_with_half_spread(store, 1.0)
    assert enter(root, snapshots, entry_desk, fly_order("t3", lots=2)).outcome == OUTCOME_OPENED


def test_a_rerun_returns_the_recorded_outcome(root, store, snapshots, entry_desk):
    snapshot_with_half_spread(store, 3.0)
    first = enter(root, snapshots, entry_desk, fly_order())
    assert enter(root, snapshots, entry_desk, fly_order()) == first


def test_the_limit_comes_only_from_c2_s_decision_on_this_exact_proposal(root, store, snapshots, entry_desk):
    """Judge 68: no caller can pass a looser limit. The order has no limit field; the decision must be C2's on this
    proposal (a decision on another proposal, e.g. 1 lot for a 2-lot order, or one without entry cash is refused)."""
    snapshot_with_half_spread(store, 3.0)
    assert "approved_entry_rs" not in EntryOrder.__dataclass_fields__
    one_lot = approved(fly_proposal("t1", lots=1))
    for order in (fly_order("t1", lots=2, risk=one_lot),
                  fly_order("t1", risk=replace(approved(fly_proposal("t1")), entry_cash_rs=None))):  # fmt: skip
        result = enter(root, snapshots, entry_desk, order)
        assert result.outcome == OUTCOME_REFUSED and "exact proposal" in result.reason
        DeskRecords(PaperAccount(root, BOOK1_RULES)).events.path.unlink()  # a fresh attempt for the next case
    assert PaperAccount(root, BOOK1_RULES).fills() == []


def test_c2_records_the_approved_entry_cash_with_the_same_cost_model(root, tmp_path):
    margins = tmp_path / "margins.csv"
    margins.write_text(",".join(MARGIN_COLUMNS) + "\nSF,200,40000,0,0,test calculator,2026-10-13\n")
    stressed = {"factor_file": str(factor_file(1.5, date(2026, 10, 12)))}  # the day before the decision
    cfg = load_app_config(overrides={"risk": {"stressed_margin": stressed}})
    proposal = fly_proposal()
    market = decision_market()
    decision = build_risk_manager(cfg, root, tables=local_tables(margins)).evaluate(
        proposal, load_risk_book(root, BOOK1_RULES, market, {}), market
    )
    assert decision.ok and decision.proposal == proposal
    assert decision.entry_cash_rs == approved_entry(proposal) == decision.record()["entry_cash_rs"]
