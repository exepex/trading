"""Story G6 revision 2 (judge 98 addendum 2; owner decision "3 B"): the operative claim rule E+D, its calibrated
critical values, the committed size study and threshold tables, and the real-data skew they rest on."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

from fno.constants import V1_RV_1S, V6_BIG_MOVE_5S
from fno.forecast_v4.confirmatory import MIN_CLAIM_BATCHES, batch_means_p, calibrated_p

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import v4_claim_thresholds as thresholds  # noqa: E402
import v4_size_study as study  # noqa: E402

DIFFERENCES = [0.004 * math.sin(t) + 0.002 * (t % 3 - 1) - 0.0004 for t in range(60)]


def test_calibrated_p_meets_the_first_step_exactly_when_the_batch_p_meets_the_threshold():
    step = 0.02 / 15
    p_t = batch_means_p(DIFFERENCES, 5)  # 12 batches of 5
    assert calibrated_p(DIFFERENCES, 5, p_t, step) == pytest.approx(step)
    assert calibrated_p(DIFFERENCES, 5, p_t * 0.999, step) > step
    assert calibrated_p(DIFFERENCES, 5, p_t * 1.001, step) < step
    assert calibrated_p(DIFFERENCES, 5, 1e-12, step) == 1.0  # capped


def test_no_claim_below_twelve_batches_or_without_a_threshold():
    assert MIN_CLAIM_BATCHES == 12
    assert calibrated_p(DIFFERENCES[:59], 5, 0.5, 0.002) == 1.0  # 11 batches
    assert calibrated_p(DIFFERENCES, 5, 0.0, 0.002) == 1.0


def test_conservative_rank_sits_below_the_expected_count():
    assert thresholds.conservative_rank(0.02 / 15, 100_000) == 114  # 133.3 - 1.645 x 11.5
    assert thresholds.conservative_rank(1e-9, 100_000) == 0


def test_claim_threshold_is_zero_below_twelve_batches_and_deterministic_otherwise():
    nulls = thresholds.empirical_nulls()
    assert thresholds.claim_threshold(V1_RV_1S, 55, 0.02, series=2_000, nulls=nulls) == 0.0
    first = thresholds.claim_threshold(V6_BIG_MOVE_5S, 125, 0.02, series=2_000, nulls=nulls)
    assert first == thresholds.claim_threshold(V6_BIG_MOVE_5S, 125, 0.02, series=2_000, nulls=nulls) and first > 0


def test_outcomes_needed_reproduces_the_plain_first_step_and_grows_as_the_threshold_falls():
    assert thresholds.outcomes_needed(0.02 / 15, 3) == 134
    assert thresholds.outcomes_needed(1e-9, 3) > 400 and thresholds.outcomes_needed(0.0, 3) is None


def test_committed_threshold_table_is_within_tolerance_in_every_cell_and_matches_its_markdown():
    data = json.loads((ROOT / "research/forecasts/v4_claim_thresholds.json").read_text(encoding="utf-8"))
    assert len(data["rows"]) == 5 * 3 * 2 and all(r["held_out_size"] <= r["tolerance"] for r in data["rows"])
    text = (ROOT / "research/forecasts/v4_claim_thresholds.md").read_text(encoding="utf-8")
    assert text == thresholds.markdown(data["rows"])


def test_committed_size_study_covers_its_plan_and_matches_its_markdown():
    data = json.loads((ROOT / "research/forecasts/v4_size_study.json").read_text(encoding="utf-8"))
    assert [(c["process"], c["block"], c["n"]) for c in data["cells"]] == study.plan()
    assert (data["small_tier"], data["large_tier"]) == (100_000, 10_000)
    assert (ROOT / "research/forecasts/v4_size_study.md").read_text(encoding="utf-8") == study.markdown(data)


def test_the_empirical_nulls_are_centred_and_as_skewed_as_the_protocol_says():
    def skew(d):
        return float((d**3).mean() / (d**2).mean() ** 1.5)

    h1, h5 = study.real_differences(1), study.real_differences(5)
    assert abs(h1.mean()) < 1e-12 and len(h1) == 685
    assert round(skew(h1), 1) == 15.0 and round(skew(h5), 1) == 8.8
    assert skew(study.brier_differences(1)) > 0 and skew(study.brier_differences(5)) > 0  # right-skewed orientation
