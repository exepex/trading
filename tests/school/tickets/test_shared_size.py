"""Criterion 3 (story MS-P1f; judge 481 finding 2 and the orchestrator's rulings): a displayed size shared by
several accounts is served whole fill by whole fill in a seeded order that favours no name, accounts before tickets;
an unservable account entry is `unavailable: size_shared`."""

from dataclasses import replace
from datetime import timedelta

import pytest

from fno.school.constants import SIDE_BUY, SIDE_SELL, Outcome, RefusalReason, RoadCode, TicketReason, UnavailableReason
from fno.school.contracts.accounts import FilledLeg, FillResult
from fno.school.tickets.rules import as_ticket
from fno.school.tickets.shared_size import OwnedFill, allocate, allocation_seed, fill_status
from tests.school.contracts import builders as b

AT = b.SLOT_AT + timedelta(minutes=4)
SELL_SIDE = replace(b.quote(size=60), ask_qty=999)  # bid 60: what a sell meets
BUY_SIDE = replace(b.quote(4.0, 5.0, size=45), bid_qty=999)  # ask 45: what a buy meets
SNAP = b.snapshot(quotes={b.key(1000.0): SELL_SIDE, b.key(900.0): BUY_SIDE})


def spread(owner: str, units: int, is_ticket: bool = False) -> OwnedFill:
    legs = (FilledLeg(b.key(1000.0), SIDE_SELL, units, 10.0, 0.0), FilledLeg(b.key(900.0), SIDE_BUY, units, 5.0, 0.0))
    return OwnedFill(owner, FillResult(legs, filled_at=AT, rests_on="cd" * 32), is_ticket)


def test_two_accounts_on_one_displayed_size_one_is_served_and_the_order_is_recorded():
    allocation = allocate([spread("CS1@1", 30), spread("REF@1", 30)], SNAP, "15:00")
    assert len(allocation.servable) == 1 and len(allocation.unservable) == 1
    assert allocation.order == tuple(o.owner for o in (*allocation.servable, *allocation.unservable))
    assert allocation.seed == allocation_seed(SNAP, "15:00") and len(allocation.seed) == 64


def test_the_order_does_not_depend_on_the_order_given_and_is_reproducible():
    one = allocate([spread("CS1@1", 30), spread("REF@1", 30)], SNAP, "15:00")
    two = allocate([spread("REF@1", 30), spread("CS1@1", 30)], SNAP, "15:00")
    assert one.order == two.order == allocate([spread("CS1@1", 30), spread("REF@1", 30)], SNAP, "15:00").order


def test_no_name_wins_every_session():
    sessions = [b.SESSION + timedelta(days=d) for d in range(40)]
    winners = {allocate([spread("CS1@1", 30), spread("REF@1", 30)], replace(SNAP, session=s), "15:00").order[0]
               for s in sessions}  # fmt: skip
    assert winners == {"CS1@1", "REF@1"}, "the seed changes with the session, so neither name always wins"


def test_the_seed_changes_with_the_road_and_the_slot():
    other_road = replace(SNAP, road=RoadCode.NIFTY_MONTHLY)
    seeds = {allocation_seed(SNAP, "15:00"), allocation_seed(other_road, "15:00"), allocation_seed(SNAP, "15:20")}
    assert len(seeds) == 3


def test_accounts_are_served_before_tickets_whatever_the_seed():
    for days in range(20):
        snap = replace(SNAP, session=b.SESSION + timedelta(days=days))
        allocation = allocate([spread("A@1", 45, is_ticket=True), spread("Z@1", 45)], snap, "15:00")
        assert [o.owner for o in allocation.servable] == ["Z@1"] and allocation.unservable[0].is_ticket


def test_fills_that_fit_together_are_all_servable():
    allocation = allocate([spread("CS1@1", 15), spread("REF@1", 30)], SNAP, "15:00")  # 45 buys exactly
    assert len(allocation.servable) == 2 and allocation.unservable == ()


def test_one_owner_may_exit_and_reenter_on_one_snapshot():
    allocation = allocate([spread("CS1@1", 30), spread("CS1@1", 30)], SNAP, "15:00")
    assert len(allocation.servable) == 1 and len(allocation.unservable) == 1


def test_refusals_use_no_size_and_no_fills_give_an_empty_allocation():
    refused = OwnedFill("CS1@1", FillResult(refused=(RefusalReason.MISSING_QUOTE,)))
    allocation = allocate([refused, spread("REF@1", 45)], SNAP, "15:00")
    assert [o.owner for o in allocation.servable] == ["REF@1"] and allocation.unservable == ()
    assert allocate([], SNAP, "15:00").servable == allocate([refused], SNAP, "15:00").servable == ()


def test_a_contract_absent_from_the_snapshot_serves_nothing():
    assert allocate([spread("CS1@1", 1)], b.snapshot(quotes={}), "15:00").unservable


def test_an_unservable_account_entry_is_unavailable_size_shared_even_when_both_fills_are_equal():
    first, second = spread("CS1@1", 30), spread("REF@1", 30)
    assert first.fill == second.fill
    allocation = allocate([first, second], SNAP, "15:00")
    served, lost = allocation.servable[0], allocation.unservable[0]
    assert fill_status(b.decision(served.owner), served.fill, allocation) == (Outcome.TRADE, "")
    assert fill_status(b.decision(lost.owner), lost.fill, allocation) == (Outcome.UNAVAILABLE,
                                                                          UnavailableReason.SIZE_SHARED)  # fmt: skip
    refused = FillResult(refused=(RefusalReason.MISSING_QUOTE,))
    assert fill_status(b.decision(), refused, allocation) == (Outcome.REFUSED, RefusalReason.MISSING_QUOTE)


def test_only_an_account_trade_has_a_fill_status():
    with pytest.raises(ValueError):
        fill_status(as_ticket(b.decision(), TicketReason.TRADE_LIMIT), spread("CS1@1", 1).fill,
                    allocate([], SNAP, "15:00"))  # fmt: skip
