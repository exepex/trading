"""Part b's Black-76 sensitivities against finite differences of B1's own price, at a non-zero rate, both kinds."""

import pytest

from fno.school.instructor.attribution.greeks import greeks, implied_vol, price

CASES = [("CE", 1000.0, 1020.0), ("PE", 1000.0, 1020.0), ("CE", 1000.0, 950.0), ("PE", 900.0, 1010.0)]


@pytest.mark.parametrize("kind, strike, forward", CASES)
def test_each_greek_matches_the_finite_difference_of_the_price(kind, strike, forward):
    years, rate, sigma, h = 0.06, 0.065, 0.21, 1e-3
    value = lambda f=forward, t=years, s=sigma: price(f, strike, kind, t, rate, s)  # noqa: E731
    g = greeks(forward, strike, kind, years, rate, sigma)
    assert g.delta == pytest.approx((value(forward + h) - value(forward - h)) / (2 * h), rel=1e-5)
    assert g.gamma == pytest.approx((value(forward + h) - 2 * value() + value(forward - h)) / h**2, rel=1e-3)
    assert g.vega == pytest.approx((value(s=sigma + 1e-6) - value(s=sigma - 1e-6)) / 2e-6, rel=1e-5)
    assert g.theta == pytest.approx(-(value(t=years + 1e-7) - value(t=years - 1e-7)) / 2e-7, rel=1e-4)


def test_the_volatility_is_recovered_from_its_own_price():
    mid = price(1000.0, 1000.0, "PE", 0.06, 0.065, 0.21)
    assert implied_vol(mid, 1000.0, 1000.0, "PE", 0.06, 0.065) == pytest.approx(0.21, abs=1e-7)
