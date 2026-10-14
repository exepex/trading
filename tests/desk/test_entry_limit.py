"""Story E4, entry limit (orchestrator, 14 Oct 2026): a trade opens only when its net entry at the execution snapshot's
touch is no worse than the entry C2 approved (decision mids, B2's Rs 1 pad, entry charges); otherwise nothing fills,
with the reason `entry_worse_than_approved` and the shortfall recorded."""

from dataclasses import replace

import pytest

from fno.books.account import PaperAccount
from fno.config import load_app_config
from fno.constants import (
    BOOK1_RULES,
    ENTRY_WORSE_THAN_APPROVED,
    OUTCOME_NOT_OPENED,
    OUTCOME_OPENED,
    OUTCOME_REFUSED,
    SIDE_BUY,
)
from fno.costs import order_charges
from fno.desk.entries import EntryOrder
from fno.desk.records import DeskRecords
from fno.research_engine.structures import BOUGHT
from fno.risk.book_view import load_risk_book
from fno.risk.wiring import build_risk_manager

from .builders import (
    CHARGES,
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


def test_a_rs_2_wider_half_spread_on_all_four_legs_fills_nothing_and_logs_the_shortfall(root, store, snapshots,
                                                                                      entry_desk):  # fmt: skip
    snapshot_with_half_spread(store, 1.0 + 2.0)  # C2 assumed Rs 1 each way; the market charges Rs 3
    result = enter(root, snapshots, entry_desk, fly_order())
    approved = approved_entry(fly_proposal())
    assert approved == pytest.approx(net_at_touch(1.0))  # C2's modelled entry = the touch at a Rs 1 half-spread
    assert result.outcome == OUTCOME_NOT_OPENED and result.reason.startswith(ENTRY_WORSE_THAN_APPROVED)
    assert result.shortfall_rs == pytest.approx(approved - net_at_touch(3.0))
    assert abs(result.shortfall_rs - 4 * 2.0 * LOT) < 5  # Rs 520 of spread; charges shift a little (STT falls)
    assert PaperAccount(root, BOOK1_RULES).fills() == []
    [event] = DeskRecords(PaperAccount(root, BOOK1_RULES)).event_rows("t1")
    assert float(event["shortfall_rs"]) == result.shortfall_rs


@pytest.mark.parametrize("half", [1.0, 0.5, 0.05])
def test_an_entry_equal_to_or_better_than_the_approved_one_fills(root, store, snapshots, entry_desk, half):
    snapshot_with_half_spread(store, half)
    result = enter(root, snapshots, entry_desk, fly_order())
    assert result.outcome == OUTCOME_OPENED and result.shortfall_rs is None
    assert PaperAccount(root, BOOK1_RULES).summary()["cash_rs"] == pytest.approx(500_000 + net_at_touch(half))


def test_a_paisa_worse_than_approved_fills_nothing(root, store, snapshots, entry_desk):
    snapshot_with_half_spread(store, 1.0)
    result = enter(root, snapshots, entry_desk, fly_order(limit=approved_entry(fly_proposal()) + 0.01))
    assert result.outcome == OUTCOME_NOT_OPENED and result.shortfall_rs == pytest.approx(0.01)


def test_the_limit_scales_with_the_lots(root, store, snapshots, entry_desk):
    snapshot_with_half_spread(store, 3.0)
    for lots in (1, 2):
        order = fly_order(f"t{lots}", lots=lots)
        assert order.risk.entry_cash_rs == pytest.approx(approved_entry(fly_proposal(lots=lots)))
        result = enter(root, snapshots, entry_desk, order)
        assert result.shortfall_rs == pytest.approx(order.risk.entry_cash_rs - net_at_touch(3.0, lots))
    shortfalls = [float(e["shortfall_rs"]) for e in DeskRecords(PaperAccount(root, BOOK1_RULES)).event_rows()]
    assert shortfalls[1] == pytest.approx(2 * shortfalls[0], abs=2)  # twice the units, twice the shortfall


def test_a_rerun_returns_the_recorded_shortfall(root, store, snapshots, entry_desk):
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
    margins.write_text("structure,width,margin_per_lot_rs,source,as_of\nSF,200,40000,test calculator,2026-10-13\n")
    stressed = {"multiplier": 1.5, "source": "test factor", "as_of": "2026-10-13"}
    cfg = load_app_config(overrides={"risk": {"margins": {"file": str(margins)}, "stressed_margin": stressed}})
    proposal = fly_proposal()
    market = decision_market()
    decision = build_risk_manager(cfg, root).evaluate(proposal, load_risk_book(root, BOOK1_RULES, market, {}), market)
    assert decision.ok and decision.proposal == proposal
    assert decision.entry_cash_rs == approved_entry(proposal) == decision.record()["entry_cash_rs"]
