"""Criterion 3 (story MS-P1f): a displayed size shared by several accounts is counted, and a report never sums fills
that the size could not have served: whole fills only, never part of a structure."""

from dataclasses import replace
from datetime import timedelta

from fno.constants import SIDE_BUY, SIDE_SELL
from fno.school.constants import RefusalReason
from fno.school.contracts.accounts import FilledLeg, FillResult
from fno.school.tickets.shared_size import OwnedFill, allocate
from tests.school.contracts import builders as b

AT = b.SLOT_AT + timedelta(minutes=4)
SELL_SIDE = replace(b.quote(size=60), ask_qty=999)  # bid 60: what a sell meets
BUY_SIDE = replace(b.quote(4.0, 5.0, size=45), bid_qty=999)  # ask 45: what a buy meets
SNAP = b.snapshot(quotes={b.key(1000.0): SELL_SIDE, b.key(900.0): BUY_SIDE})


def spread(owner: str, units: int) -> OwnedFill:
    legs = (FilledLeg(b.key(1000.0), SIDE_SELL, units, 10.0, 0.0), FilledLeg(b.key(900.0), SIDE_BUY, units, 5.0, 0.0))
    return OwnedFill(owner, FillResult(legs, filled_at=AT, rests_on="cd" * 32))


def test_the_second_account_on_one_displayed_size_is_not_servable():
    allocation = allocate([spread("REF@1", 30), spread("CS1@1", 30)], SNAP)
    assert [o.owner for o in allocation.servable] == ["CS1@1"]  # fixed order: by owner
    assert [o.owner for o in allocation.unservable] == ["REF@1"] and allocation.contended


def test_fills_that_fit_together_are_all_servable():
    allocation = allocate([spread("CS1@1", 15), spread("REF@1", 30)], SNAP)  # 45 buys exactly
    assert len(allocation.servable) == 2 and not allocation.contended


def test_one_owner_may_exit_and_reenter_on_one_snapshot():
    allocation = allocate([spread("CS1@1", 30), spread("CS1@1", 30)], SNAP)
    assert len(allocation.servable) == 1 and len(allocation.unservable) == 1


def test_refusals_use_no_size_and_no_fills_give_an_empty_allocation():
    refused = OwnedFill("CS1@1", FillResult(refused=(RefusalReason.MISSING_QUOTE,)))
    allocation = allocate([refused, spread("REF@1", 45)], SNAP)
    assert [o.owner for o in allocation.servable] == ["REF@1"] and allocation.unservable == ()
    assert allocate([], SNAP) == allocate([refused], SNAP)


def test_a_contract_absent_from_the_snapshot_serves_nothing():
    assert allocate([spread("CS1@1", 1)], b.snapshot(quotes={})).unservable
