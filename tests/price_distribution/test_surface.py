"""G13 criteria 2-3: the ATM IV, IV at delta points (never extrapolated), the 25-delta risk reversal and butterfly, and
the 30-day IV from the frozen G1 interpolation."""

import pytest

from fno.forecast.iv30 import interpolate_30d
from fno.price_distribution.chain import SpreadFilter, used_quotes
from fno.price_distribution.surface import SmilePoint, iv_at_delta, surface
from fno.price_distribution.valuation import value_day
from tests.price_distribution.builders import DAY, FORWARD, NEAR, NEXT, RATE, chain_day, expiry_chain, flat


def smile(strike):
    return 0.12 + 0.6 * ((strike / FORWARD) - 1) ** 2 - 0.15 * ((strike / FORWARD) - 1)


def test_atm_iv_is_the_mean_of_the_call_and_put_ivs_at_the_strike_nearest_the_forward():
    used = used_quotes(expiry_chain(vol=smile), SpreadFilter())
    found = surface(used, FORWARD, (NEAR - DAY).days, RATE)
    assert found.atm_strike == 23_000 and found.atm_iv == pytest.approx(smile(23_000), abs=1e-7)


def test_a_tie_takes_the_lower_strike():
    used = used_quotes(expiry_chain(forward=23_025.0), SpreadFilter())
    assert surface(used, 23_025.0, 11, RATE).atm_strike == 23_000


def test_delta_points_are_linear_in_delta_and_missing_outside_the_quoted_deltas():
    points = (SmilePoint(22_500, "PE", 0.15, -0.20), SmilePoint(22_700, "PE", 0.13, -0.30),
              SmilePoint(23_400, "CE", 0.11, 0.28))  # fmt: skip
    assert iv_at_delta(points, -0.25) == pytest.approx(0.14)
    assert iv_at_delta(points, -0.10) is None  # beyond the furthest put
    assert iv_at_delta(points, 0.25) is None  # one call only, not at 0.25
    assert iv_at_delta(points, 0.28) == 0.11


def test_risk_reversal_and_butterfly_from_the_25_delta_points():
    found = surface(used_quotes(expiry_chain(vol=smile), SpreadFilter()), FORWARD, 11, RATE)
    put25, call25 = found.delta_ivs["25P"], found.delta_ivs["25C"]
    assert put25 > found.atm_iv > call25  # a put skew
    assert found.risk_reversal_25 == pytest.approx(call25 - put25)
    assert found.butterfly_25 == pytest.approx((call25 + put25) / 2 - found.atm_iv)


def test_a_flat_smile_has_no_skew():
    found = surface(used_quotes(expiry_chain(vol=flat(0.12)), SpreadFilter()), FORWARD, 11, RATE)
    assert found.risk_reversal_25 == pytest.approx(0.0, abs=1e-6) and found.butterfly_25 == pytest.approx(0.0, abs=1e-6)


def test_the_30_day_iv_is_the_frozen_interpolation_of_the_record_s_atm_ivs():
    day = value_day(chain_day((expiry_chain(NEAR, flat(0.11)), expiry_chain(NEXT, flat(0.14), 23_100.0))),
                    SpreadFilter(), RATE)  # fmt: skip
    atm = {e.expiry: e.surface.atm_iv * 100 for e in day.expiries}
    assert day.iv30 == interpolate_30d(DAY, atm) and not day.iv30.flagged
    single = value_day(chain_day((expiry_chain(NEXT, flat(0.14), 23_100.0),)), SpreadFilter(), RATE)
    assert single.iv30.flagged and single.iv30.points == pytest.approx(14.0, abs=1e-5)
