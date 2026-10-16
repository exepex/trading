"""G13 criterion 11: the quantile score and calibration by hand, nothing scored before its target close, labels and
methods never pooled, and the comparison equal to G4's bootstrap called directly (not tested under 40 paired days)."""

from datetime import date, timedelta

import pytest

from fno.forecast_scoring.block_bootstrap import compare
from fno.price_distribution.constants import FORECAST_LEVELS
from fno.price_distribution.score_report import comparison_seed, comparisons, group_scores, resolved, score_report
from fno.price_distribution.scoring import pinball, quantile_score, share_below, share_inside

QUANTILES = [-0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03]


@pytest.mark.parametrize(
    ("level", "outcome", "quantile", "loss"),
    [(0.05, -0.05, -0.03, 0.019), (0.05, 0.0, -0.03, 0.0015), (0.5, 0.01, 0.01, 0.0), (0.95, 0.04, 0.03, 0.0095)],
)
def test_pinball_by_hand_below_above_and_at_the_quantile(level, outcome, quantile, loss):
    assert pinball(level, outcome, quantile) == pytest.approx(loss)


def test_the_quantile_score_is_twice_the_mean_pinball():
    by_hand = 2 / 7 * sum(pinball(t, 0.015, q) for t, q in zip(FORECAST_LEVELS, QUANTILES, strict=True))
    assert quantile_score(FORECAST_LEVELS, 0.015, QUANTILES) == pytest.approx(by_hand)
    assert quantile_score(FORECAST_LEVELS, 0.0, QUANTILES) < quantile_score(FORECAST_LEVELS, 0.05, QUANTILES)


def test_calibration_shares_by_hand_and_empty():
    assert share_below([0.0, 0.1, -0.1, 0.2], [0.05, 0.05, 0.05, 0.05]) == 0.5
    assert share_inside([0.0, 0.1, -0.03], [-0.03] * 3, [0.03] * 3) == pytest.approx(2 / 3)  # the edge counts inside
    assert share_below([], []) is None and share_inside([], [], []) is None


def row(day, forecaster="implied", label="backfill_eod", method="aa", shift=0.0, status="ok"):
    out = {"day": day.isoformat(), "forecaster": forecaster, "horizon": "h1", "label": label, "status": status,
           "method_sha256": method * 32, "target_day": (day + timedelta(days=1)).isoformat(), "s_ref": 100.0,
           "tail_levels": []}  # fmt: skip
    return out | {f"lq{round(t * 100):02d}": q + shift for t, q in zip(FORECAST_LEVELS, QUANTILES, strict=True)}


def test_a_row_is_scored_only_once_its_target_close_exists_and_only_when_ok():
    day = date(2026, 1, 5)
    rows = [row(day), row(day + timedelta(days=1)), row(day + timedelta(days=2), status="missing")]
    closes = {day + timedelta(days=1): 101.0, day + timedelta(days=3): 99.0}
    found = resolved(rows, closes)
    assert [(r["day"], round(y, 6)) for r, y in found] == [(day.isoformat(), round(0.00995033, 6))]


def test_labels_and_methods_are_never_pooled():
    day, closes = date(2026, 1, 5), {date(2026, 1, 6): 100.5}
    scored = resolved([row(day), row(day, label="live"), row(day, method="bb")], closes)
    assert {(g["label"], g["method"]) for g in group_scores(scored)} == {("backfill_eod", "a" * 8), ("live", "a" * 8),
                                                                          ("backfill_eod", "b" * 8)}  # fmt: skip


def test_the_comparison_is_g4_s_bootstrap_on_the_paired_daily_differences():
    days = [date(2025, 1, 1) + timedelta(days=i) for i in range(60)]
    closes = {d + timedelta(days=1): 100 * (1 + 0.01 * ((i % 7) - 3)) for i, d in enumerate(days)}
    rows = [row(d) for d in days] + [row(d, "rv20", shift=0.004) for d in days] + [row(d, "hist750") for d in days[:30]]
    out = comparisons(resolved(rows, closes))
    implied = {r["day"]: quantile_score(FORECAST_LEVELS, y, [r[f"lq{round(t * 100):02d}"] for t in FORECAST_LEVELS])
               for r, y in resolved([row(d) for d in days], closes)}  # fmt: skip
    rv = {r["day"]: quantile_score(FORECAST_LEVELS, y, [r[f"lq{round(t * 100):02d}"] for t in FORECAST_LEVELS])
          for r, y in resolved([row(d, "rv20", shift=0.004) for d in days], closes)}  # fmt: skip
    direct = compare(
        [implied[d] - rv[d] for d in sorted(implied)], comparison_seed("backfill_eod", "a" * 8, "h1", "rv20")
    )
    first, second = out
    assert (first["second"], first["n"], first["p_value"], first["tested"]) == ("rv20", 60, direct.p_value, True)
    assert direct.interval == first["interval_unadjusted_95"]
    assert first["mean_difference"] == pytest.approx(direct.mean_difference)
    assert (second["second"], second["n"], second["tested"], second["p_value"]) == ("hist750", 30, False, 1.0)


def test_an_empty_report_has_no_groups():
    assert score_report([], {}) | {"note": ""} == {"schema": "g13_scores_v1", "note": "", "closes_through": None,
                                                    "scored_rows": 0, "groups": [], "comparisons": []}  # fmt: skip


def test_a_comparison_s_seed_does_not_move_when_another_group_appears():
    days = [date(2025, 1, 1) + timedelta(days=i) for i in range(60)]
    closes = {d + timedelta(days=1): 100 * (1 + 0.01 * ((i % 7) - 3)) for i, d in enumerate(days)}
    rows = [row(d) for d in days] + [row(d, "rv20", shift=0.004) for d in days]
    alone = comparisons(resolved(rows, closes))[0]
    earlier = [row(d, label="a_first") for d in days] + [row(d, "rv20", label="a_first") for d in days]
    together = [c for c in comparisons(resolved(rows + earlier, closes)) if c["label"] == "backfill_eod"][0]
    assert (alone["comparison"], alone["p_value"]) == (together["comparison"], together["p_value"])
