"""Story MS-P1m: C2's own `MarginRoom`, unchanged, on the school's margin: every open trade and the proposal priced on
their own legs; it passes with the room exactly enough and refuses one rupee short; a trade it cannot price refuses."""

import pytest

from fno.nse_margins.road_margin import ArchivedSpanMargin
from fno.nse_margins.road_trades import RoadTradeTerms, road_open_trade, road_proposal
from fno.risk.inputs import OpenTrade, RiskInputError, TradeTerms
from fno.risk.rules import MarginRoom
from tests.risk.builders import book, contract, market
from tests.risk.test_rules import FixedCosts

from .span_builder import DAY, EXPIRY
from .test_road_margin import PCS_LEGS, SF_LEGS, source, terms


def CONTRACT(underlying, expiry, leg):  # the market builder's contract ids
    return contract(leg.strike, leg.kind, expiry)


HELD, NEW = terms("SF", 100.0, 1, legs=SF_LEGS), terms("PCS", 100.0, 2, legs=PCS_LEGS)


def _check(cash: float, held_terms=HELD):
    margin = ArchivedSpanMargin(source())
    if isinstance(held_terms, RoadTradeTerms):
        held = road_open_trade("held", held_terms, CONTRACT, 0.0)
    else:  # a trade the school margin cannot price
        held = OpenTrade("held", held_terms, {CONTRACT("NIFTY", EXPIRY, leg): leg.side * 65 for leg in SF_LEGS}, 0.0)
    prices = {(leg.strike, leg.kind): 0.0 for leg in (*SF_LEGS, *NEW.legs)}
    verdict = MarginRoom(margin, FixedCosts(0.0)).check(road_proposal("new", NEW, CONTRACT),
                                                       book([held], cash=cash, marked=cash),
                                                       market(20_000.0, prices, EXPIRY, day=DAY))  # fmt: skip
    return verdict, margin.margin(HELD, DAY) + margin.margin(NEW, DAY)


def test_c2_s_room_counts_every_trade_on_its_own_legs_and_holds_at_the_rupee():
    _, needed = _check(1.0)
    inside, _ = _check(needed)
    outside, _ = _check(needed - 1.0)
    assert inside.ok and inside.numbers["needed_rs"] == pytest.approx(needed)
    assert inside.numbers["method"] == "archived_span_per_trade" and not outside.ok


def test_an_open_trade_the_school_margin_cannot_price_refuses_the_proposal():
    with pytest.raises(RiskInputError, match="carries no legs"):
        _check(1e9, TradeTerms("SF", 100.0, 1))
