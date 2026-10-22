"""Criterion 3 (story MS-P1f): a displayed size shared by several accounts is counted, and a report never sums fills
that the size could not have served."""

from dataclasses import replace
from datetime import timedelta

from fno.constants import SIDE_BUY, SIDE_SELL
from fno.school.contracts.accounts import FilledLeg, FillResult
from fno.school.tickets.shared_size import SizeClaim, servable_units, size_claims
from tests.school.contracts import builders as b

AT = b.SLOT_AT + timedelta(minutes=4)
SELL_SIDE = replace(b.quote(size=60), ask_qty=999)  # bid 60: what a sell meets
BUY_SIDE = replace(b.quote(4.0, 5.0, size=45), bid_qty=999)  # ask 45: what a buy meets
SNAP = b.snapshot(quotes={b.key(1000.0): SELL_SIDE, b.key(900.0): BUY_SIDE})


def sold(units: int) -> FillResult:
    legs = (FilledLeg(b.key(1000.0), SIDE_SELL, units, 10.0, 0.0), FilledLeg(b.key(900.0), SIDE_BUY, units, 5.0, 0.0))
    return FillResult(legs, filled_at=AT, rests_on="cd" * 32)


def test_two_accounts_on_one_displayed_size_are_counted_with_the_excess():
    claims = size_claims({"CS1@1": sold(30), "REF@1": sold(30)}, SNAP)
    assert claims == (SizeClaim(b.key(900.0), SIDE_BUY, 45, 60, ("CS1@1", "REF@1")),
                      SizeClaim(b.key(1000.0), SIDE_SELL, 60, 60, ("CS1@1", "REF@1")))  # fmt: skip
    assert [c.excess for c in claims] == [15, 0]
    assert servable_units(claims) == 105, "never the 120 the accounts filled"


def test_within_the_displayed_size_nothing_is_excess():
    claims = size_claims({"CS1@1": sold(30)}, SNAP)
    assert [c.excess for c in claims] == [0, 0] and servable_units(claims) == 60


def test_refusals_add_nothing_and_no_fills_give_no_claims():
    refused = FillResult(refused=("missing_quote",))
    assert size_claims({"CS1@1": refused}, SNAP) == () and size_claims({}, SNAP) == ()


def test_a_contract_absent_from_the_snapshot_shows_zero_size():
    claims = size_claims({"CS1@1": sold(30)}, b.snapshot(quotes={}))
    assert {c.displayed for c in claims} == {0} and servable_units(claims) == 0
