"""Story G8 criterion 3: a real 2024-25 V6b comparison (a constant base-rate-like forecaster against an EWMA-style
forecaster built here from the committed closes) equals direct calls of `fno/forecast_v4`; the regime line equals
`window_regime` on the scored days' first-session VIX and returns."""

import math
from datetime import date

import pytest

from fno.constants import V6_BIG_MOVE_5S
from fno.forecast_scoring.v4.comparison import compare, paired_rows, seed_word
from fno.forecast_v4.bootstrap import hac_one_sided_p, one_sided_test, relative_improvement
from fno.forecast_v4.confirmatory import batch_means_p, studentized_bootstrap_p
from fno.forecast_v4.pairs import pair_probability
from fno.forecast_v4.regime import window_regime
from fno.forecast_v4.terms import FAMILY_SIZE, family_seed_word
from tests.forecast_scoring_v4.helpers import regular_closes, v6b_outcomes, values

BASE_RATE_2017_26 = 0.1376  # disclosed 5-session base rate (protocol section 8)


@pytest.fixture(scope="module")
def real():
    sessions = regular_closes(date(2024, 1, 1), date(2025, 6, 30))
    outcomes = v6b_outcomes(sessions)
    days = [s[0] for s in sessions]
    variance, ewma = 1e-4, {}
    for i in range(1, len(sessions)):
        r = math.log(sessions[i][1] / sessions[i - 1][1])
        variance = 0.94 * variance + 0.06 * r * r
        sigma5 = math.sqrt(variance * 5)
        ewma[days[i]] = min(0.99, 2 * (1 - 0.5 * (1 + math.erf(0.02 / sigma5 / math.sqrt(2)))) * 2.5)
    baseline = {d: BASE_RATE_2017_26 for d in days}
    baseline[days[3]] = None  # a baseline gap: counted, never filled
    return sessions, outcomes, values(ewma), values(baseline)


def test_a_real_v6b_comparison_equals_direct_calls(real):
    sessions, outcomes, forecaster, baseline = real
    rows = paired_rows(forecaster, baseline, outcomes)
    k = seed_word(V6_BIG_MOVE_5S, "rules", "v6_ewma_t4")
    c = compare(V6_BIG_MOVE_5S, "v6_ewma_t4", "base_rate", rows, outcomes, k)
    direct = pair_probability(rows)
    d = direct.scored.differences
    assert c.pairing == direct and len(d) > 300
    assert (direct.unresolved, direct.missing_baseline, direct.missing_forecast) == (5, 1, 1)  # last 5; day 3; day 0
    assert c.mean_difference == pytest.approx(sum(d) / len(d))
    assert c.relative_improvement == relative_improvement(direct.gate)
    assert c.batch_means_p == batch_means_p(d, 10) and c.studentized_p == studentized_bootstrap_p(d, 10, k)
    assert c.centred_bootstrap_p == one_sided_test(d, 10, k).p_value and c.hac_p == hac_one_sided_p(d, 10)
    days = direct.scored.days
    expected = window_regime([outcomes[x].vix for x in days], [outcomes[x].log_return for x in days])
    assert c.regime == expected and c.regime.big_days > 5
    assert c.power is not None and c.power.n_scored == len(d)


def test_seed_words_members_first_then_stable_numbers_after_the_family():
    assert seed_word(V6_BIG_MOVE_5S, "rules", "x") == family_seed_word(V6_BIG_MOVE_5S, "rules")
    other = seed_word(V6_BIG_MOVE_5S, None, "v6_ewma_t4")
    assert other > FAMILY_SIZE and other == seed_word(V6_BIG_MOVE_5S, None, "v6_ewma_t4")


def test_an_empty_comparison_has_no_window_and_no_values():
    c = compare(V6_BIG_MOVE_5S, "f", "base_rate", [], {}, 99)
    assert c.mean_difference is None and c.regime is None and c.power is None and c.relative_improvement is None
    assert c.batch_means_p == 1.0 and c.hac_p is None
