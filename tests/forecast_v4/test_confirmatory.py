"""Story G6 revision 1 (ChatGPT review 99): the confirmatory test (max of batch-means t and studentized block
bootstrap), the Student t function it needs, a small seeded null calibration, the committed full calibration, and the
EOD proxy's drift diagnostic."""

from __future__ import annotations

import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from fno.forecast_v4.confirmatory import batch_means_p, confirmatory_test, studentized_bootstrap_p
from fno.forecast_v4.diagnostics import proxy_drift
from fno.forecast_v4.student_t import t_cdf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import v4_null_calibration as calibration  # noqa: E402

DIFFERENCES = [0.004 * math.sin(t) + 0.002 * (t % 3 - 1) - 0.0004 for t in range(60)]
COMMITTED = {"batch": 0.18643304085532486, "studentized": 0.3194680531946805}  # block 10, comparison 4


@pytest.mark.parametrize(
    ("t", "df", "expected"),
    [(2.0, 5, 0.9490302605850709), (-1.0, 1, 0.25), (0.0, 3, 0.5), (-3.0, 9, 0.0074781819552071), (1.96, 1e6, 0.975)],
)
def test_student_t_matches_known_values(t, df, expected):
    assert t_cdf(t, df) == pytest.approx(expected, abs=2e-6 if df > 1e5 else 1e-12)


def test_batch_means_p_matches_a_hand_t_test_on_the_latest_whole_batches():
    x = np.asarray(DIFFERENCES[:57])  # 5 batches of 10; the earliest 7 dropped
    batches = x[7:].reshape(5, 10).mean(axis=1)
    t = batches.mean() / (batches.std(ddof=1) / math.sqrt(5))
    assert batch_means_p(x, 10) == pytest.approx(t_cdf(t, 4), abs=1e-15)


def test_confirmatory_p_is_the_larger_of_the_two_and_reproduces_committed_values():
    assert batch_means_p(DIFFERENCES, 10) == COMMITTED["batch"]
    assert studentized_bootstrap_p(DIFFERENCES, 10, 4) == COMMITTED["studentized"]
    result = confirmatory_test(DIFFERENCES, 10, 4)
    assert result.tested and result.p_value == max(COMMITTED.values())


def test_confirmatory_test_is_not_run_below_two_blocks_or_on_constant_differences():
    assert confirmatory_test(DIFFERENCES[:19], 10, 1).p_value == 1.0
    assert not confirmatory_test(DIFFERENCES[:19], 10, 1).tested
    assert batch_means_p([0.0] * 40, 10) == 1.0 and studentized_bootstrap_p([0.0] * 40, 10, 1) == 1.0


def test_a_clear_improvement_is_still_detected():
    better = [d - 0.004 for d in DIFFERENCES]
    assert confirmatory_test(better, 10, 1).p_value < 0.002


def test_small_seeded_null_calibration_confirmatory_within_tolerance_centred_over_rejects():
    """CI-sized version of tools/v4_null_calibration.py: 200 i.i.d. and AR(1) series at n = 2L = 20."""
    for kind in ("iid", "ar1"):
        cell = calibration.run_cell(kind, 10, 20, cell=0, series=200, resamples=500)
        five = calibration.THRESHOLDS.index(0.05)
        assert cell["rates"]["confirmatory_max"][five] <= calibration.tolerance(0.05, 200)
        assert cell["rates"]["centred_rev0"][five] > 0.15  # why revision 0's test was replaced


def test_the_committed_full_calibration_covers_every_cell_and_test():
    data = json.loads((ROOT / "research/forecasts/v4_null_calibration.json").read_text(encoding="utf-8"))
    assert (data["seed"], data["series"]) == (calibration.SEED, 1_000)
    cells = {(c["kind"], c["block"], c["n"]) for c in data["cells"]}
    assert cells == {(k, b, n) for k in calibration.KINDS for b in calibration.BLOCKS for n in (2 * b, 125)}
    assert all(set(c["rates"]) == set(calibration.TESTS) for c in data["cells"])
    assert (ROOT / "research/forecasts/v4_null_calibration.md").read_text(encoding="utf-8") == calibration.markdown(
        data["cells"], data["series"]
    )


def test_proxy_drift_reports_paired_ratios_and_never_pairs_a_missing_value():
    start = date(2026, 11, 2)
    days = [(start + timedelta(n), 0.15, 0.15) for n in range(30)] + [(start + timedelta(40), None, 0.15)]
    days += [(start + timedelta(50 + n), 0.165, 0.15) for n in range(20)]
    drift = proxy_drift(days)
    assert drift.pairs == 50 and drift.median_ratio == pytest.approx(1.0)
    assert drift.recent_median_ratio == pytest.approx(1.1) and drift.drift == pytest.approx(0.1)
    assert proxy_drift([]).pairs == 0 and proxy_drift([]).drift is None
