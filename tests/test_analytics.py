import math

from fno import analytics as an


def test_put_call_parity():
    s, k, t, r, v = 22500, 22600, 30 / 365, 0.065, 0.14
    c = an.bs_price(s, k, t, r, v, "CE")
    p = an.bs_price(s, k, t, r, v, "PE")
    assert math.isclose(c - p, s - k * math.exp(-r * t), abs_tol=1e-6)


def test_implied_vol_round_trip():
    price = an.bs_price(22500, 22500, 14 / 365, 0.065, 0.13, "CE")
    assert math.isclose(an.implied_vol(price, 22500, 22500, 14 / 365, 0.065, "CE"), 0.13, abs_tol=1e-4)


def test_greeks_signs():
    g = an.bs_greeks(22500, 22500, 14 / 365, 0.065, 0.13, "PE")
    assert -0.6 < g.delta < -0.4 and g.gamma > 0 and g.theta < 0 and g.vega > 0


def test_rsi_extremes():
    assert an.rsi(list(range(1, 40))) == 100.0
    assert an.rsi(list(range(40, 1, -1))) < 1


def test_historical_vol_flat_series_is_zero():
    assert an.historical_vol([100.0] * 30) == 0.0
