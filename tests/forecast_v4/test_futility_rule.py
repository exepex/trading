"""Story G6 revision 3: the operative futility rule F+D and the false-futility study behind it (a false "no" gets the
false-"yes" standard)."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from fno.constants import V1_RV_1S, V6_BIG_MOVE_5S
from fno.forecast_v4.bootstrap import effect_check
from fno.forecast_v4.confirmatory import FUTILITY_LEVEL, batch_means_p, futility_p
from fno.forecast_v4.pairs import PairedSet

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import v4_futility_study as study  # noqa: E402

D = np.array([0.004 * math.sin(t) + 0.002 * (t % 3 - 1) - 0.0004 for t in range(60)])
B = np.array([0.02 + 0.005 * math.cos(t) for t in range(60)])


def test_futility_p_tests_improvement_below_the_effect_and_maps_onto_the_level():
    excess = -(D + 0.03 * B)
    p_e = batch_means_p(excess, 5)
    assert futility_p(D, B, 5, 0.03, p_e) == pytest.approx(FUTILITY_LEVEL)
    assert futility_p(D, B, 5, 0.03, p_e * 1.01) < FUTILITY_LEVEL < futility_p(D, B, 5, 0.03, p_e * 0.99)


def test_a_large_true_improvement_is_never_futile_and_a_null_one_is():
    better, flat = D - 0.01, D * 0.01 + 0.0
    assert futility_p(better, B, 5, 0.03, 0.01) == 1.0 or futility_p(better, B, 5, 0.03, 0.01) > FUTILITY_LEVEL
    assert futility_p(flat, B, 5, 0.03, 0.01) <= FUTILITY_LEVEL  # improvement about zero, effect 3%


def test_no_futility_below_twelve_batches_or_without_a_threshold():
    assert futility_p(D[:59], B[:59], 5, 0.03, 0.5) == 1.0
    assert futility_p(D, B, 5, 0.03, 0.0) == 1.0


@pytest.mark.parametrize("look", study.LOOKS)
def test_the_fast_f0_bound_equals_effect_check(look):
    gate = PairedSet(tuple(range(60)), tuple(D), tuple(B))
    expected = effect_check(gate, 0.03, 10, 4, look).upper_bound
    assert study.f0_upper(D, B, 10, 4, look) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("question", [V1_RV_1S, V6_BIG_MOVE_5S])
def test_nulls_sit_exactly_at_the_minimum_effect_in_both_orientations(question):
    d, base = study.pairs_for(question)
    margin = study.QUESTIONS[question][3]
    for flip in (False, True):
        shifted = study.at_minimum_effect(d, base, margin, flip)
        assert -shifted.mean() / base.mean() == pytest.approx(margin, abs=1e-12)


def test_committed_futility_table_matches_its_markdown_and_f_plus_d_holds_the_target():
    data = json.loads((ROOT / "research/forecasts/v4_futility_study.json").read_text(encoding="utf-8"))
    assert len(data["cells"]) == 4 * 2 * 2 and data["target"] == pytest.approx(0.025)
    tolerance = study.study.tolerance(data["target"], data["fd_series"])
    assert all(c["fd"] <= tolerance for c in data["cells"])
    assert (ROOT / "research/forecasts/v4_futility_study.md").read_text(encoding="utf-8") == study.markdown(data)
