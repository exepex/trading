"""Story BR1a: the outcome screen, the legacy spot proxy, study 1's rule, the look counts and study 3's procedure,
on hand-made fixtures (criteria 4, 5, 6, 6b and 7)."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

STUDIES = Path(__file__).resolve().parents[2] / "research" / "breadth" / "studies"
sys.path.insert(0, str(STUDIES))

from brstudy import daily, panel, study1, study3  # noqa: E402
from brstudy.stats import look_counts  # noqa: E402

from fno.forecast_v4.confirmatory import confirmatory_test  # noqa: E402


def row(day, spot, implied="0.01", strikes="2026-01-29=100.0;110.0;120.0", source="udiff", next_spot=""):
    return {"day": day, "spot": str(spot), "implied": implied, "strikes": strikes, "source": source,
            "next_spot": next_spot}  # fmt: skip


def test_a_replaced_strike_set_is_excluded_and_a_crash_with_every_strike_kept_is_scored():
    days = ["2026-01-05", "2026-01-06", "2026-01-07"]
    split = {days[0]: row(days[0], 2000), days[1]: row(days[1], 400, strikes="2026-01-29=20.0;22.0;24.0")}
    crash = {days[0]: row(days[0], 100), days[1]: row(days[1], 80)}
    assert daily.outcomes(split, days)[days[0]] is None  # outcome-side: read from t+1's strikes
    assert daily.outcomes(crash, days)[days[0]][0] == 1  # -22% log move, scored


def test_the_legacy_outcome_uses_the_same_near_month_contract_across_a_roll():
    jan = {"day": "2019-01-31", "underlying": "X", "proxy_expiry": "2019-02-28"}
    feb = {"day": "2019-02-01", "underlying": "X", "proxy_expiry": "2019-02-28"}
    rows = [
        {**jan, "futures": "2019-01-31=100.0|2019-02-28=101.0"},
        {**feb, "futures": "2019-02-28=101.5|2019-03-28=102.5"},
    ]
    linked = panel.link_next(rows)
    assert linked[0]["next_spot"] == "101.5"  # the Feb contract on both days, not Jan's expiring one
    assert linked[0]["source"] == panel.LEGACY


def test_the_primary_is_the_lowest_mean_brier_with_ties_to_the_earlier_baseline():
    scored = {"A": {"2024-01-02": (1, {"market": 0.5, "trail60": 0.5, "cal60": 0.1})}}  # Brier 0.25, 0.25, 0.81
    losses = [{"day": f"2024-01-{d:02d}", "market": 0.25, "trail60": 0.25, "cal60": 0.01} for d in range(2, 22)]
    result = study1.primary_baseline(scored, losses, study1.FALLBACK_WINDOW)
    assert result["primary"] == "market"  # 0.25 = 0.25 at 4 decimals: the earlier one
    assert result["delta"] == pytest.approx(0.02 * 0.25)


def test_the_look_counts_follow_the_formula_by_hand():
    variance, delta = 0.02**2 * (1.2 / 0.8), 0.004
    z = 2.474740 + 0.841621  # z(1 - 0.02 / 3) + z(0.8)
    assert look_counts(0.02, variance, delta) == (math.ceil(math.ceil(z * z * variance / delta**2) / 2),
                                                  math.ceil(z * z * variance / delta**2))  # fmt: skip
    assert look_counts(0.01, variance, delta)[1] > look_counts(0.02, variance, delta)[1]  # a lower rate, later looks


def test_every_series_of_a_path_uses_the_same_block_starts():
    days = 200
    members = np.stack([m * 1000 + np.arange(days, dtype=float) for m in range(3)])
    losses = 5000 + np.arange(days, dtype=float)
    paths, loss_paths = study3.population_paths(members, losses, 150, 0)
    raw = study3.block_paths(days, study3.PATHS, 150, 0)
    for m in range(3):
        decoded = paths[m] + members[m].mean() - m * 1000  # undo the centring and the member's code
        np.testing.assert_array_equal(decoded, raw)
    np.testing.assert_array_equal(loss_paths - 5000, raw)


def test_each_null_series_is_centred_within_the_population_tested():
    whole = np.zeros((3, 500))
    whole[0, 250:] = 0.01  # a real edge in the second year only
    worst_year = whole[:, 250:]
    assert np.allclose(study3.centred(worst_year).mean(axis=1), 0)
    assert study3.centred(whole)[0, 250:].mean() > 0  # centring on the whole history would leave the edge in


def _result(rate, plus, minus):
    return {"rate": rate, "false_claim": {"whole/+d": plus, "whole/-d": minus}}


def test_the_loop_skips_a_rate_that_fails_only_for_minus_d():
    good, bad = {"look1": 0.01, "look2": 0.02, "either": 0.03}, {"look1": 0.01, "look2": 0.03, "either": 0.04}
    results = [_result(0.02, good, bad), _result(0.015, good, good)]
    assert study3.select_rate(results) == 0.015
    assert study3.select_rate([_result(0.005, bad, bad)]) is None  # postponed


def test_the_bootstrap_shortcut_gives_the_same_decisions_as_the_full_test():
    rng = np.random.default_rng(7)
    paths = rng.standard_normal((3, 40, 120)) - 0.25  # a strong effect: many members pass the batch-means screen
    rate, looks = 0.05, (60, 120)
    shortcut = study3.false_claims(paths, looks, rate)
    full = {look: [] for look in looks}
    for i in range(paths.shape[1]):
        for look in looks:
            ps = [confirmatory_test(paths[m, i, :look], 5, m).p_value for m in range(3)]
            full[look].append(min(ps) <= rate / 3)
    assert shortcut["look1"] == np.mean(full[60]) and shortcut["look2"] == np.mean(full[120])


def test_false_futility_counts_a_true_improvement_of_delta_in_each_signs_own_direction():
    rng = np.random.default_rng(3)
    member_paths = rng.standard_normal((3, 50, 100)) * 0.001
    losses = np.full((50, 100), 0.2)
    far = study3.false_futility(member_paths - 0.05, losses, 100, 0.004, 0.025)  # a huge true improvement
    assert far == 0.0
    assert study3.false_futility(member_paths + 0.05, losses, 100, 0.004, 0.025) == 1.0  # a huge loss: futile
