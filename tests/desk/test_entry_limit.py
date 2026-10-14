"""Story E4, entry limit (orchestrator, 14 Oct 2026): a trade opens only when its net entry at the execution snapshot's
touch is no worse than the entry C2 approved (decision mids, B2's Rs 1 pad, entry charges); otherwise nothing fills,
with the reason `entry_worse_than_approved` and the shortfall recorded."""

import pytest

from fno.books.account import PaperAccount
from fno.constants import BOOK1_RULES, ENTRY_WORSE_THAN_APPROVED, OUTCOME_NOT_OPENED, OUTCOME_OPENED, SIDE_BUY
from fno.costs import order_charges
from fno.desk.records import DeskRecords
from fno.research_engine.structures import BOUGHT

from .builders import (
    CHARGES,
    FLY_LEGS,
    FLY_QUOTES,
    LOT,
    approved_entry,
    at,
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
        assert order.approved_entry_rs == pytest.approx(approved_entry(fly_proposal(lots=lots)))
        result = enter(root, snapshots, entry_desk, order)
        assert result.shortfall_rs == pytest.approx(order.approved_entry_rs - net_at_touch(3.0, lots))
    shortfalls = [float(e["shortfall_rs"]) for e in DeskRecords(PaperAccount(root, BOOK1_RULES)).event_rows()]
    assert shortfalls[1] == pytest.approx(2 * shortfalls[0], abs=2)  # twice the units, twice the shortfall


def test_a_rerun_returns_the_recorded_shortfall(root, store, snapshots, entry_desk):
    snapshot_with_half_spread(store, 3.0)
    first = enter(root, snapshots, entry_desk, fly_order())
    assert enter(root, snapshots, entry_desk, fly_order()) == first
