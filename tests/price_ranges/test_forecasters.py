"""G13b criterion 3: each forecaster by hand: `implied` scaled from G13's distribution with P(up) = 1 - CDF(S_ref),
`rv20`, `hist750`, `ewma_t4` with G7's `Ewma`, the `no_change` point mass, and their not-eligible cases."""

import math
from statistics import NormalDist

import numpy as np
import pytest

from fno.forecast_v4_rules.baselines import Ewma
from fno.forecast_v4_rules.series import close_proxy_rv
from fno.price_distribution.chain import SpreadFilter
from fno.price_distribution.valuation import value_day
from fno.price_ranges.constants import LEVELS, MISSING, NOT_ELIGIBLE, OK, REST_OF_DAY
from fno.price_ranges.forecasters import (
    EwmaT4Range,
    HistoricalRange,
    ImpliedRange,
    NoChangeRange,
    RangeInputs,
    RealisedVolRange,
)
from fno.price_ranges.t4 import t4_quantile
from tests.price_distribution.builders import DAY, NEAR, NEXT, RATE, chain_day
from tests.price_ranges.builders import closes

HISTORY = tuple(closes())
S_REF = 22_990.0


def inputs(history=HISTORY, valuation=None, to_expiry=None, tail=REST_OF_DAY):
    return RangeInputs(DAY, S_REF, tail, history, valuation, to_expiry or {})


def test_implied_is_g13s_distribution_scaled_around_its_median_with_p_up_from_its_cdf():
    valuation = value_day(chain_day(), SpreadFilter(), RATE)
    near = valuation.usable()[0]
    found, forward = near.distribution.distribution, near.forward
    out = ImpliedRange().forecast(inputs(valuation=valuation, to_expiry={NEAR: 6, NEXT: 25}), 3)
    share = (3 + REST_OF_DAY) / (6 + REST_OF_DAY)
    median = math.log(found.quantile(0.5)[0] / forward)
    centre = share * (math.log(forward / S_REF) + median)
    expected = [centre + math.sqrt(share) * (math.log(found.quantile(t)[0] / forward) - median) for t in LEVELS]
    assert out.status == OK and out.log_quantiles == pytest.approx(expected)
    k0 = forward * math.exp(median - centre / math.sqrt(share))
    assert out.p_up == pytest.approx(1 - found.cdf(k0))
    assert 0 < out.p_big_move < 1


def test_implied_takes_the_shortest_expiry_long_enough_and_is_missing_without_one():
    valuation = value_day(chain_day(), SpreadFilter(), RATE)
    assert ImpliedRange().forecast(inputs(valuation=valuation, to_expiry={NEAR: 2, NEXT: 25}), 3).status == OK
    out = ImpliedRange().forecast(inputs(valuation=valuation, to_expiry={NEAR: 2, NEXT: 2}), 3)
    assert (out.status, out.reason) == (MISSING, "no expiry with a distribution and at least 3 sessions after the day")
    assert ImpliedRange().forecast(inputs(valuation=None), 1).status == MISSING


def test_rv20_is_lognormal_at_the_last_20_returns_over_tau():
    window = HISTORY[-21:]
    sd = math.sqrt(sum(math.log(b.value / a.value) ** 2 for a, b in zip(window, window[1:], strict=False)) / 20)
    out = RealisedVolRange().forecast(inputs(), 3)
    expected = [NormalDist().inv_cdf(t) * sd * math.sqrt(3 + REST_OF_DAY) for t in LEVELS]
    assert out.log_quantiles == pytest.approx(expected) and out.p_up == 0.5


@pytest.mark.parametrize(("n", "status"), [(21, OK), (20, NOT_ELIGIBLE), (0, NOT_ELIGIBLE)])
def test_rv20_needs_21_closes(n, status):
    assert RealisedVolRange().forecast(inputs(HISTORY[len(HISTORY) - n :] if n else ()), 1).status == status


def test_hist750_is_the_empirical_quantile_and_its_p_up_the_share_of_rises():
    window = HISTORY[-750:]
    returns = [math.log(b.value / a.value) for a, b in zip(window, window[3:], strict=False)]
    out = HistoricalRange().forecast(inputs(), 3)
    assert out.log_quantiles == pytest.approx(list(np.quantile(returns, LEVELS)))
    assert out.p_up == pytest.approx(sum(r > 0 for r in returns) / len(returns))


@pytest.mark.parametrize(("n", "status"), [(501, OK), (500, NOT_ELIGIBLE)])  # 500 one-session returns at 501 closes
def test_hist750_needs_500_returns(n, status):
    assert HistoricalRange().forecast(inputs(HISTORY[-n:]), 1).status == status


def test_ewma_t4_is_g7s_ewma_variance_times_a_unit_variance_t4():
    s2 = Ewma(close_proxy_rv(list(HISTORY))).variance(DAY)  # the last session before the day: HISTORY's last
    out = EwmaT4Range().forecast(inputs(), 1)
    expected = [t4_quantile(t) / math.sqrt(2) * math.sqrt(s2 * (1 + REST_OF_DAY)) for t in LEVELS]
    assert out.log_quantiles == pytest.approx(expected) and out.p_up == 0.5
    assert EwmaT4Range().forecast(inputs(HISTORY[-200:]), 1).status == NOT_ELIGIBLE  # Ewma seeds at 250


def test_no_change_is_a_point_mass_at_s_ref():
    out = NoChangeRange().forecast(inputs(()), 3)
    assert out.status == OK and out.log_quantiles == (0.0,) * 5 and out.p_up == 0.5
