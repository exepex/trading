"""Judge 489's two minors (story MS-P1e): every ranked card's estimate is pinned at 0.0, and a missing quote gives
`no_valid_quotes` on every family, not only the ladder."""

from dataclasses import replace

import pytest

from fno.school.constants import NoTradeReason, Outcome, RoadCode
from tests.school.drivers import builders as b

RANKED = ("CS1", "DB1", "DR1", "WS1", "PS2", "PS3", "PS4", "REF")  # cards that carry an estimate
UNRANKED = ("PS5", "KL1", "RC1", "N0")  # never ranked: no estimate on the card


@pytest.mark.parametrize("code", RANKED)
def test_a_ranked_card_pins_its_estimate_at_zero(code):
    """There is no honest estimate (EDGE1 found no edge). A card with 500 here must fail until a recorded decision
    changes it together with this test."""
    assert b.cards()[code].parameters["expected_net_rs"] == 0.0


@pytest.mark.parametrize("code", UNRANKED)
def test_an_unranked_card_carries_no_estimate(code):
    assert "expected_net_rs" not in b.cards()[code].parameters


def without_quotes(snapshot, expiries):
    return replace(snapshot, quotes={k: q for k, q in snapshot.quotes.items() if k.expiry not in expiries})


CASES = {  # code: (road, scene arguments, history)
    "CS1": (b.scene(), b.history([b.SPOT - 1] * 20)),
    "DB1": (b.scene(), b.history([b.SPOT * (1.05 if i % 2 else 0.95) for i in range(20)])),
    "DR1": (b.scene(), b.history([b.SPOT - 500] * 19 + [b.SPOT])),
    "WS1": (b.scene(RoadCode.NIFTY_WEEKLY, 25_000.0, 50.0, 75, (3,), vol=0.4), ()),
    "PS2": (b.scene(), ()),
    "PS3": (b.scene(), ()),
    "PS4": (b.scene(), ()),
    "REF": (b.scene(), ()),
    "RC1": (b.scene(), ()),
    "PS5": (b.scene(days=(45, 75)), ()),
    "KL1": (b.scene(RoadCode.NIFTY_MONTHLY, 25_000.0, 50.0, 75, (45, 75)), ()),
}


@pytest.mark.parametrize("code", sorted(CASES))
def test_every_driver_says_no_valid_quotes_when_the_road_has_none_and_trades_with_them(code):
    (road_day, snapshot), history = CASES[code]
    driver = b.drivers()[code]
    assert driver.decide(road_day, snapshot, history, ()).outcome == Outcome.TRADE, "the fixture day does trade"
    bare = without_quotes(snapshot, set(road_day.expiries))
    decision = driver.decide(road_day, bare, history, ())
    assert (decision.outcome, decision.reason) == (Outcome.NO_TRADE, NoTradeReason.NO_VALID_QUOTES)


def test_ref_uses_the_next_expiry_when_the_nearest_has_no_quotes():
    (road_day, snapshot), _ = CASES["REF"]
    decision = b.drivers()["REF"].decide(road_day, without_quotes(snapshot, {road_day.expiries[0]}), (), ())
    assert decision.outcome == Outcome.TRADE
    assert {leg.key.expiry for leg in decision.proposal.legs} == {road_day.expiries[1]}


def test_a_structure_that_is_listed_but_over_the_cap_is_not_a_quote_problem():
    (road_day, snapshot), _ = CASES["PS4"]
    driver = b.drivers()["PS4"]
    driver.builder = type(driver.builder)(driver.builder.costs, 100.0)
    decision = driver.decide(road_day, snapshot, (), ())
    assert decision.reason == NoTradeReason.NO_STRUCTURE_UNDER_CAP
