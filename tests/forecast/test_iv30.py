"""Story G1 criterion 2: the 30-day ATM implied volatility against hand computations on two fixture days (bracketed
and not bracketed), and B1's look-ahead harness on real days.

Fixture day d = Mon 2 Mar 2026, NIFTY 22,000 (ATM strike 22,000). Monthly expiries (futures listed that day): 18 Mar
(16 days, future 22,050) and 15 Apr (44 days, future 22,120). Option closes are Black-76 prices at known volatilities:
18 Mar call 12%, put 14% (ATM IV 13%); 15 Apr call and put 15% (ATM IV 15%).
Bracketed, by hand: w1 = 0.13^2 x 16 = 0.2704; w2 = 0.15^2 x 44 = 0.99; w30 = 0.2704 + 0.7196 x 14 / 28 = 0.6302;
IV30 = sqrt(0.6302 / 30) = 0.144937, 14.4937 points.
Not bracketed: the 15 Apr put did not trade, so the 18 Mar expiry (16 days, at least 7) is used alone: 13.0, flagged.
"""

import math
import sys
from datetime import date, timedelta
from pathlib import Path
from random import Random

import pytest

from fno.forecast.iv30 import AtmIv30Feature, PanelAtmIv30, interpolate_30d
from fno.research_data.panel_reader import FutureQuote, NiftyPanel, OptionQuote, SessionClose
from fno.research_engine.features import DecisionContext
from fno.research_engine.implied_vol import Black76, OptionPricing

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_engine"))
from lookahead_harness import assert_no_lookahead  # noqa: E402

RATE, SPOT, D = 0.065, 22000.0, date(2026, 3, 2)
E1, E2 = date(2026, 3, 18), date(2026, 4, 15)
FUTURES = {E1: 22050.0, E2: 22120.0}
VOLS = {(E1, "CE"): 0.12, (E1, "PE"): 0.14, (E2, "CE"): 0.15, (E2, "PE"): 0.15}
ESTIMATOR = PanelAtmIv30(Black76(), RATE)


def _price(expiry: date, strike: float, kind: str) -> float:
    sigma = VOLS.get((expiry, kind), 0.2)
    pricing = OptionPricing(0.0, FUTURES[expiry], strike, kind, (expiry - D).days / 365, RATE)
    return round(Black76().price(pricing, sigma), 6)


def _panel(untraded: frozenset = frozenset()) -> NiftyPanel:
    quotes = tuple(
        OptionQuote(e, k, kind, _price(e, k, kind), 0.0, 0 if (e, kind) in untraded else 1000, 1)
        for e in (E1, E2)
        for k in (21950.0, 22000.0, 22050.0)
        for kind in ("CE", "PE")
    )
    futures = tuple(FutureQuote(e, f, f, 500, 1) for e, f in FUTURES.items())
    return NiftyPanel((SessionClose(D, "regular", SPOT, 15.0),), {D: quotes}, {D: futures})


def test_bracketed_day_matches_the_hand_computation():
    estimate = ESTIMATOR.estimate(_panel(), D)
    assert estimate.flagged is False and estimate.expiries == (E1, E2)
    assert estimate.points == pytest.approx(math.sqrt((0.2704 + 0.7196 * 14 / 28) / 30) * 100, abs=1e-5)
    assert estimate.points == pytest.approx(14.4937, abs=1e-4)


def test_not_bracketed_day_uses_the_nearest_expiry_alone_flagged():
    estimate = ESTIMATOR.estimate(_panel(untraded=frozenset({(E2, "PE")})), D)
    assert estimate.flagged is True and estimate.expiries == (E1,)
    assert estimate.points == pytest.approx(13.0, abs=1e-5)


def test_exactly_30_days_uses_that_expiry_unflagged():
    e30 = D + timedelta(days=30)
    assert interpolate_30d(D, {E1: 13.0, e30: 15.0, E2: 20.0}).points == pytest.approx(15.0)


def test_fallback_needs_7_days_and_a_tie_goes_to_the_longer_expiry():
    near, broken, far = D + timedelta(days=23), D + timedelta(days=25), D + timedelta(days=37)
    tie = interpolate_30d(D, {near: 10.0, broken: None, far: 12.0})  # bracket (25, 37) broken; 23 and 37 tie
    assert tie.flagged and tie.expiries == (far,) and tie.points == 12.0
    assert interpolate_30d(D, {D + timedelta(days=6): 11.0, far: None}) is None  # 6 days is too short
    assert interpolate_30d(D, {}) is None


def test_an_expiry_on_its_last_day_is_not_the_near_bracket():
    """0 days left has no implied volatility; the next monthly alone is used, flagged."""
    estimate = interpolate_30d(D, {D: None, E2: 15.0})
    assert estimate.flagged and estimate.expiries == (E2,)


@pytest.fixture(scope="module")
def real_data():
    from fno.composition import load_research_data

    return load_research_data((2025, 2026), keep=lambda day, expiry: (expiry - day).days <= 100)


def test_no_lookahead_on_10_random_real_days(real_data):
    """B1's harness: every panel value after the day's close is changed or removed; IV30 must not move."""
    feature = AtmIv30Feature(ESTIMATOR)
    days = [s.day for s in real_data.panel.sessions if date(2025, 1, 15) <= s.day <= date(2026, 9, 10)]
    values = []
    for day in sorted(Random(20261013).sample(days, 10)):
        context = DecisionContext(day, day, day)  # unused by this feature
        values.append(assert_no_lookahead(feature, real_data, day, context, trials=2))
    assert all(v is not None and 5 < v < 40 for v in values)
