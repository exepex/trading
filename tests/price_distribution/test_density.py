"""G13 criterion 4: the implied distribution. A flat-IV chain gives back Black-76's lognormal; noise is pooled with
equal weights; a pair over 200 points apart forms no midpoint; a quantile is linear in strike; the tails keep the edge
mass; too few points or a mean off the forward is missing with its reason; the mean is exact."""

import pytest

from fno.analytics import norm_cdf
from fno.price_distribution.chain import ExpiryChain, Quote, SpreadFilter, UsedQuotes, used_quotes
from fno.price_distribution.constants import BODY, MAX_MEAN_GAP, TAIL
from fno.price_distribution.density import (
    Distribution,
    Tail,
    implied_distribution,
    pool_adjacent_violators,
    put_curve,
    raw_cdf,
)
from fno.price_distribution.pricing import d1_d2
from tests.price_distribution.builders import FORWARD, NEAR, RATE, expiry_chain, flat, strikes

DAYS = 11


def flat_distribution(sigma=0.12, grid=None):
    used = used_quotes(expiry_chain(NEAR, flat(sigma), grid=grid), SpreadFilter())
    return implied_distribution(used, FORWARD, RATE, DAYS)


def lognormal_cdf(strike, sigma=0.12):
    return norm_cdf(-d1_d2(FORWARD, strike, sigma, DAYS)[1])


def test_a_flat_iv_chain_gives_back_the_lognormal_within_0002():
    found = flat_distribution().distribution
    assert max(abs(c - lognormal_cdf(k)) for k, c in found.points) < 0.002
    for level, (strike, _) in found.quantiles().items():
        assert lognormal_cdf(strike) == pytest.approx(level, abs=0.002)
    assert found.raw_decreases == 0


def test_the_tails_are_continuous_at_the_edge_and_follow_the_formula():
    found = flat_distribution(grid=strikes(22_600, 23_400)).distribution
    lo, hi = found.lower, found.upper
    assert found.cdf(lo.strike - 1e-6) == pytest.approx(lo.cdf, abs=1e-6)
    assert found.cdf(hi.strike + 1e-6) == pytest.approx(hi.cdf, abs=1e-6)
    far = lo.strike - 500
    expected = lo.cdf * lognormal_cdf(far, lo.vol) / lognormal_cdf(lo.strike, lo.vol)
    assert found.cdf(far) == pytest.approx(expected)
    q01, source = found.quantile(0.01)
    assert source == TAIL and found.cdf(q01) == pytest.approx(0.01, abs=1e-9)
    assert found.quantile(0.5)[1] == BODY


def test_pool_adjacent_violators_weighs_every_point_the_same():
    assert pool_adjacent_violators([0.1, 0.5, 0.3, 0.6]) == pytest.approx([0.1, 0.4, 0.4, 0.6])
    assert pool_adjacent_violators([0.3, 0.2, 0.1]) == pytest.approx([0.2, 0.2, 0.2])


def _gap_weighted(values, weights):
    blocks = []
    for v, w in zip(values, weights, strict=True):
        blocks.append([v, w, 1])
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            v2, w2, n2 = blocks.pop()
            v1, w1, n1 = blocks.pop()
            blocks.append([(v1 * w1 + v2 * w2) / (w1 + w2), w1 + w2, n1 + n2])
    return [v for v, _, n in blocks for _ in range(n)]


def test_noise_across_unequal_gaps_is_pooled_equally_not_by_gap():
    grid = [k for k in strikes(22_400, 23_600) if k not in (22_950, 23_000)]  # a 150-point gap 22,900-23,050
    chain = expiry_chain(NEAR, flat(0.12), grid=grid)
    bumped = tuple(Quote(q.strike, q.kind, q.price + 6, q.bid + 6, q.ask + 6) if (q.strike, q.kind) ==
                   (22_900, "PE") else q for q in chain.quotes)  # fmt: skip
    used = used_quotes(ExpiryChain(NEAR, bumped, None), SpreadFilter())
    raw = raw_cdf(put_curve(used, FORWARD, RATE, DAYS), RATE, DAYS)
    values, gaps = [c for _, c, _, _ in raw], [b - a for _, _, a, b in raw]
    found = implied_distribution(used, FORWARD, RATE, DAYS).distribution
    pooled = [c for _, c in found.points]
    assert found.raw_decreases >= 1
    assert pooled == pytest.approx(pool_adjacent_violators(values))
    assert pooled != pytest.approx(_gap_weighted(values, gaps))


def test_a_pair_over_200_points_apart_forms_no_midpoint_before_the_pass():
    grid = [k for k in strikes(22_400, 23_600) if not 22_850 < k < 23_100]  # a 250-point gap
    curve = put_curve(used_quotes(expiry_chain(NEAR, flat(0.12), grid=grid), SpreadFilter()), FORWARD, RATE, DAYS)
    midpoints = [m for m, _, _, _ in raw_cdf(curve, RATE, DAYS)]
    assert (22_850 + 23_100) / 2 not in midpoints and len(midpoints) == len(curve) - 2


def _distribution(points, forward=23_000.0):
    return Distribution(forward, DAYS, tuple(points), 0, Tail(points[0][0], points[0][1], 0.12),
                        Tail(points[-1][0], points[-1][1], 0.12))  # fmt: skip


def test_a_quantile_is_linear_in_strike_on_the_first_rising_segment():
    found = _distribution([(22_800, 0.1), (22_900, 0.2), (23_100, 0.4), (23_200, 0.4), (23_300, 0.9)])
    assert found.quantile(0.3) == (pytest.approx(23_000.0, abs=1e-9), BODY)  # log-strike would give 22,999.78
    assert found.quantile(0.4)[0] == pytest.approx(23_100.0)  # the first segment reaching it, not the flat one
    assert found.quantile(0.1) == (22_800, BODY)


def test_the_mean_is_exact_body_segments_plus_lognormal_partial_expectations():
    found = _distribution([(22_900, 0.2), (23_100, 0.8)])
    d1_lo, d2_lo = d1_d2(23_000.0, 22_900, 0.12, DAYS)
    d1_hi, d2_hi = d1_d2(23_000.0, 23_100, 0.12, DAYS)
    expected = (0.6 * 23_000 + 0.2 * 23_000 * norm_cdf(-d1_lo) / norm_cdf(-d2_lo)
                + 0.2 * 23_000 * norm_cdf(d1_hi) / norm_cdf(d2_hi))  # fmt: skip
    assert found.mean() == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize(("count", "ok"), [(9, True), (8, False), (0, False)])
def test_at_least_8_cdf_points(count, ok):
    grid = [22_800 + 50 * i for i in range(count)]
    used = used_quotes(expiry_chain(NEAR, flat(0.12), grid=grid), SpreadFilter()) if count else UsedQuotes((), {})
    result = implied_distribution(used, FORWARD, RATE, DAYS)
    assert (result.distribution is not None) == ok
    if not ok:
        assert result.reason.startswith("too few CDF points")


@pytest.mark.parametrize(("multiple", "ok"), [(1.5, True), (2.0, False)])  # mean 0.42% and 0.55% off
def test_a_mean_more_than_half_a_percent_off_the_forward_is_missing_with_its_reason(multiple, ok):
    chain = expiry_chain(NEAR, flat(0.12), grid=strikes(22_700, 23_300))
    priced = tuple(Quote(q.strike, q.kind, q.price * multiple, q.bid * multiple, q.ask * multiple)
                   if q.kind == "CE" and q.strike >= 23_200 else q for q in chain.quotes)  # fmt: skip
    result = implied_distribution(used_quotes(ExpiryChain(NEAR, priced, None), SpreadFilter()), FORWARD, RATE, DAYS)
    assert (result.distribution is not None) == ok
    if not ok:
        assert result.reason.startswith("mean ") and f"limit {MAX_MEAN_GAP:.1%}" in result.reason


def test_an_edge_option_without_an_implied_volatility_is_missing():
    chain = expiry_chain(NEAR, flat(0.12))
    low = min(q.strike for q in chain.quotes)
    broken = tuple(Quote(q.strike, q.kind, 0.0, 0.0, 0.01) if (q.strike, q.kind) == (low, "PE") else q
                   for q in chain.quotes)  # fmt: skip
    used = UsedQuotes(tuple(q for q in broken), {})
    result = implied_distribution(used, FORWARD, RATE, DAYS)
    assert result.distribution is None and "lower edge" in result.reason


@pytest.mark.parametrize(("gap", "kept"), [(200, True), (250, False)])
def test_a_pair_exactly_200_points_apart_still_forms_a_midpoint(gap, kept):
    grid = [k for k in strikes(22_400, 23_600) if not 22_800 < k < 22_800 + gap]
    curve = put_curve(used_quotes(expiry_chain(NEAR, flat(0.12), grid=grid), SpreadFilter()), FORWARD, RATE, DAYS)
    midpoints = [m for m, _, _, _ in raw_cdf(curve, RATE, DAYS)]
    assert ((22_800 + 22_800 + gap) / 2 in midpoints) == kept


def test_pooled_values_are_clipped_to_zero_and_one():
    chain = expiry_chain(NEAR, flat(0.12), grid=strikes(22_000, 24_000))
    low, high = 22_000, 24_000  # the lowest put far too dear, the highest call far too dear: CDF below 0 and above 1
    priced = tuple(Quote(q.strike, q.kind, q.price + 30, q.bid + 30, q.ask + 30)
                   if (q.strike, q.kind) in ((low, "PE"), (high, "CE")) else q for q in chain.quotes)  # fmt: skip
    used = used_quotes(ExpiryChain(NEAR, priced, None), SpreadFilter())
    raw = [c for _, c, _, _ in raw_cdf(put_curve(used, FORWARD, RATE, DAYS), RATE, DAYS)]
    assert min(raw) < 0 and max(raw) > 1
    points = implied_distribution(used, FORWARD, RATE, DAYS).distribution.points
    assert points[0][1] == 0.0 and points[-1][1] == 1.0 and all(0.0 <= c <= 1.0 for _, c in points)
