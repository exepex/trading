"""G13 criterion 1: the parity forward, the quote filter (at and just over its limit) and an expiry on the day."""

import math

import pytest

from fno.price_distribution.chain import (
    INVALID,
    ONE_SIDED,
    WIDE,
    ExpiryChain,
    Quote,
    SpreadFilter,
    TradedCloseFilter,
    used_quotes,
)
from fno.price_distribution.constants import MISSING, NOT_ELIGIBLE, OK
from fno.price_distribution.forward import averaged_forward, parity_forward
from fno.price_distribution.valuation import EXPIRED, NO_FORWARD, NO_QUOTES, value_expiry
from tests.price_distribution.builders import DAY, FORWARD, NEAR, RATE, expiry_chain


def test_parity_forward_is_strike_plus_grown_call_minus_put():
    assert parity_forward(23_100, 120.0, 100.0, 0.065, 11) == pytest.approx(23_100 + math.exp(0.065 * 11 / 365) * 20)


def test_the_forward_averages_the_three_strikes_with_the_closest_call_and_put():
    pairs = [(22_900, 200.0, 90.0), (23_000, 130.0, 120.0), (23_100, 80.0, 175.0), (23_200, 40.0, 240.0)]
    expected = sum(parity_forward(k, c, p, RATE, 11) for k, c, p in pairs[:3]) / 3
    assert averaged_forward(pairs, RATE, 11) == pytest.approx(expected)
    assert averaged_forward([], RATE, 11) is None


def test_a_synthetic_chain_gives_back_its_forward():
    valued = value_expiry(expiry_chain(), DAY, SpreadFilter(), RATE)
    assert valued.status == OK and valued.forward == pytest.approx(FORWARD, abs=1e-6)


@pytest.mark.parametrize(
    ("bid", "ask", "valid", "reason"),
    [
        (99.0, 101.0, True, None),  # spread 2 <= 10% of 100
        (95.0, 105.0, True, None),  # exactly 10: at the limit, used
        (94.99, 105.0, True, WIDE),  # just over
        (1.0, 1.5, True, None),  # Rs 0.50 floor, at it
        (1.0, 1.51, True, WIDE),
        (99.0, 101.0, False, INVALID),
        (None, 101.0, True, ONE_SIDED),
    ],
)
def test_the_spread_rule_at_and_just_over_its_limit(bid, ask, valid, reason):
    mid = (bid + ask) / 2 if bid is not None else None
    assert SpreadFilter().reason(Quote(23_000, "CE", mid, bid, ask, valid)) == reason


def test_end_of_day_closes_need_a_trade_and_half_a_rupee():
    rule = TradedCloseFilter()
    assert rule.reason(Quote(23_000, "CE", 0.5, volume=1)) is None
    assert rule.reason(Quote(23_000, "CE", 0.45, volume=1)) == "below_min_price"
    assert rule.reason(Quote(23_000, "CE", 10.0, volume=0)) == "no_trade"


def test_dropped_quotes_are_counted_by_reason():
    kept, wide, invalid = Quote(1, "CE", 100, 99, 101), Quote(2, "CE", 100, 80, 120), Quote(3, "PE", 5, 4, 6, False)
    chain = ExpiryChain(NEAR, (kept, wide, invalid), None)
    used = used_quotes(chain, SpreadFilter())
    assert len(used.quotes) == 1 and used.dropped == {INVALID: 1, WIDE: 1}


def test_an_expiry_on_the_day_is_not_eligible_an_empty_one_is_missing():
    today = value_expiry(ExpiryChain(DAY, expiry_chain().quotes, None), DAY, SpreadFilter(), RATE)
    assert (today.status, today.reason) == (NOT_ELIGIBLE, EXPIRED)
    empty = value_expiry(ExpiryChain(NEAR, (), None), DAY, SpreadFilter(), RATE)
    assert (empty.status, empty.reason) == (MISSING, NO_QUOTES)
    calls_only = ExpiryChain(NEAR, tuple(q for q in expiry_chain().quotes if q.kind == "CE"), None)
    assert value_expiry(calls_only, DAY, SpreadFilter(), RATE).reason == NO_FORWARD
