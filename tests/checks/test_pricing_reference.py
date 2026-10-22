"""OSS1 part a (response 319): the project's three option pricers against an outside reference, vollib's prices on a
fixed grid (`tools/vollib_reference.py` wrote the fixture; vollib is not a dependency). B1's Black-76 and C4's own
Black-76 stay two implementations (judge 83: C4 must not share the proposer's pricing); this test, which imports both,
is what keeps them equal to each other and to vollib. Spot Black-Scholes is `analytics.bs_price`."""

import json
import math
from pathlib import Path

import pytest

from fno.analytics import bs_price
from fno.checks.validity_pricing import black76 as c4_black76
from fno.checks.validity_pricing import implied_vol as c4_implied_vol
from fno.research_engine.implied_vol import Black76, OptionPricing

REFERENCE = json.loads((Path(__file__).parents[1] / "fixtures" / "pricing" / "vollib_reference.json").read_text())
ROWS = REFERENCE["rows"]
PRICE_TOLERANCE = 1e-9  # rupees; measured 4.3e-12 on 22 Oct
SIGMA_TOLERANCE = 1e-6  # B1 stops at 1e-9 in volatility; a round trip on a priced row stays far inside this
MEANINGFUL = 1.0  # rupees of time value: below it a volatility is barely determined by the price


def _time_value(row) -> float:
    """The price above its discounted intrinsic value: what the volatility moves."""
    forward, strike = row["underlying"], row["strike"]
    intrinsic = max(forward - strike, 0.0) if row["kind"] == "CE" else max(strike - forward, 0.0)
    return row["black76"] - math.exp(-row["rate"] * row["years"]) * intrinsic


def _b1(row, sigma):
    return Black76().price(_option(row, 0.0), sigma)


def _option(row, price):
    return OptionPricing(price, row["underlying"], row["strike"], row["kind"], row["years"], row["rate"])


def test_the_reference_is_vollib_s_full_grid():
    assert REFERENCE["source"].startswith("py_vollib ") and len(ROWS) == 288


def test_b1_and_c4_black76_and_spot_black_scholes_equal_vollib():
    worst = {"b1": 0.0, "c4": 0.0, "bs": 0.0}
    for row in ROWS:
        args = (row["kind"], row["underlying"], row["strike"], row["years"], row["rate"], row["sigma"])
        worst["b1"] = max(worst["b1"], abs(_b1(row, row["sigma"]) - row["black76"]))
        worst["c4"] = max(worst["c4"], abs(c4_black76(*args) - row["black76"]))
        spot = bs_price(row["underlying"], row["strike"], row["years"], row["rate"], row["sigma"], row["kind"])
        worst["bs"] = max(worst["bs"], abs(spot - row["black_scholes"]))
    assert all(gap < PRICE_TOLERANCE for gap in worst.values()), worst


@pytest.mark.parametrize("inverter", ["b1", "c4"])
def test_each_black76_inverter_recovers_the_reference_volatility(inverter):
    priced = [row for row in ROWS if _time_value(row) >= MEANINGFUL]
    assert len(priced) == 124  # every row whose volatility the price determines (the deep-in and far-out ones are not)
    for row in priced:
        if inverter == "b1":
            sigma = Black76().implied_vol(_option(row, row["black76"]))
        else:
            sigma = c4_implied_vol(row["black76"], row["kind"], row["underlying"], row["strike"], row["years"],
                                   row["rate"])  # fmt: skip
        assert sigma is not None and abs(sigma - row["sigma"]) < SIGMA_TOLERANCE, (inverter, row)
