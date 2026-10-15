"""Story G6 revision 7: the scored window's regime line, and the committed regime-stress and crash-cut tables
(judge 98 addendum 6)."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from fno.forecast_v4.regime import window_regime
from fno.forecast_v4.student_t import t_cdf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import v4_regime_stress as stress  # noqa: E402

FORECASTS = ROOT / "research" / "forecasts"


def test_the_regime_line_states_mean_vix_big_days_and_band():
    regime = window_regime([14.0, 16.0, 30.0], [0.001, -0.02, 0.0199])
    assert regime.big_days == 1 and regime.band is None and math.isclose(regime.mean_vix, 20.0)
    assert (
        regime.line() == "scored window regime: mean India VIX 20.0, 1 2% days, band below 5 (not judgeable: undecided)"
    )
    busy = window_regime([25.0] * 9, [0.03] * 9)
    assert busy.band == (8, 12) and busy.line().endswith("9 2% days, band 8-12")
    assert window_regime([20.0] * 13, [-0.025] * 13).line().endswith("band 13+")


def test_the_regime_needs_one_vix_and_one_return_per_outcome():
    with pytest.raises(ValueError):
        window_regime([15.0], [0.01, 0.02])
    with pytest.raises(ValueError):
        window_regime([], [])


@pytest.mark.parametrize(("p", "df"), [(0.025, 11), (1e-9, 24), (0.4, 49)])
def test_the_t_inversion_matches_the_batch_means_p(p, df):
    assert math.isclose(t_cdf(stress.t_at(p, df), df), p, rel_tol=1e-6)


def test_local_improvement_is_the_stretch_relative_improvement():
    d, b = np.array([-1.0, -1.0, 4.0, 4.0]), np.array([10.0, 10.0, 20.0, 20.0])
    assert stress.local_improvement(d, b, (0, 2)) == pytest.approx(0.1)
    assert stress.local_improvement(d, b, None) == pytest.approx(-0.1)


def test_the_committed_stress_table_holds_the_disclosed_figures():
    rows = json.loads((FORECASTS / "v4_regime_stress.json").read_text(encoding="utf-8"))["rows"]
    pick = {(r["question"], r["stretch"], r["n"], r["kind"], r["orientation"]): r for r in rows}
    v1 = pick[("v1_rv_next_session", "full", 125, "futility", "flipped")]
    assert round(100 * v1["rate"], 2) == 0.56 and round(100 * v1["judged"]) == 53
    v6b = pick[("v6_abs_move_2pct_within_5_sessions", "busy 250", 125, "futility", "as measured")]
    assert round(100 * v6b["rate"], 2) == 3.43 and v6b["set_truth"] > 0.02
    assert all(r["judged"] == 0 and r["rate"] == 0 for r in rows if r["stretch"].startswith("calm"))
    assert len(rows) == 4 * 5 * 2 * 2 * 2


def test_the_committed_crash_cut_table_holds_the_disclosed_costs_and_own_truth_rates():
    data = json.loads((FORECASTS / "v4_crash_cut.json").read_text(encoding="utf-8"))
    cost = {(c["question"], c["n"], c["cut"]): c for c in data["cost"]}
    v6b = cost[("v6_abs_move_2pct_within_5_sessions", 125, "vix_above_25")]
    assert round(100 * v6b["removed"], 1) == 7.6 and round(100 * v6b["judgeable_after"]) == 43
    cell = ("v6_abs_move_2pct_within_5_sessions", "busy 250", 125, "futility", "as measured")
    rows = {
        r["cut"]: r for r in data["rows"] if (r["question"], r["stretch"], r["n"], r["kind"], r["orientation"]) == cell
    }
    assert {cut: round(100 * r["conditional"], 2) for cut, r in rows.items()} == {
        "no cut": 3.48,
        "vix_above_25": 10.9,
        "big_share_above_10pct": 17.32,
    }
    assert rows["no cut"]["set_truth"] >= 0.02  # a genuine false "no"
    assert rows["vix_above_25"]["set_truth"] < 0.02 and rows["big_share_above_10pct"]["set_truth"] < 0.02  # own truth
