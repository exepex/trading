"""Story F9a criteria 3, 4, 7 and 12, by hand. 30 opportunities from 2 Nov 2026, one a day, differences
((37 i mod 11) - 4) x Rs 100 for i = 0..29: they sum to Rs 2,500, mean Rs 83.33; three are 0 (i = 1, 12, 23), so 27
changed. Cost Rs 25 an opportunity: mean net value Rs 58.33. Worst month: December (i = 29 only), Rs 200; November
holds Rs 2,300. Maximum-loss difference Rs 10 i: over the 27 changed, (4,350 - 360) / 27 = Rs 147.78."""

from datetime import date, timedelta

from fno.role_value import verdict as verdict_module
from fno.role_value.score import Opportunity, UnitScore, score_unit
from fno.role_value.verdict import COST_UNKNOWN, DROP, EARNS, INCONCLUSIVE, verdicts
from fno.scoreboard import uncertainty

D0 = date(2026, 11, 2)
DIFFS = [((i * 37) % 11 - 4) * 100.0 for i in range(30)]
REVIEW = date(2027, 6, 29)


def opportunities(max_loss_step: float = 10.0, cost: float | None = 25.0):
    return [Opportunity(D0 + timedelta(i), DIFFS[i], DIFFS[i] != 0, max_loss_step * i, cost) for i in range(30)]


def scored(p_earns, p_drop, unit="u", changed=30, cost=1.0):
    return UnitScore(unit, changed, changed, 0.0, cost, 0.0, None, p_earns, p_drop, None, None)


def test_the_score_reproduces_the_hand_computation():
    s = score_unit("macro", opportunities())
    assert (s.applicable, s.changed, s.mean_difference, s.mean_net_value) == (30, 27, 83.33, 58.33)
    assert s.worst_month == ("2026-12", 200.0) and s.mean_max_loss_difference == 147.78


def test_the_bootstrap_is_pinned_with_the_fixed_seed():
    s = score_unit("macro", opportunities())
    assert s.interval == (48.33, 101.67) and (s.p_earns, s.p_drop) == (0.0, 1.0)


def test_risk_figures_never_change_a_p_value_or_a_verdict():
    a, b = score_unit("macro", opportunities(10.0)), score_unit("macro", opportunities(-99.0))
    assert a.mean_max_loss_difference != b.mean_max_loss_difference
    assert (a.p_earns, a.p_drop) == (b.p_earns, b.p_drop)
    assert verdicts([a], True, REVIEW, [REVIEW]) == verdicts([b], True, REVIEW, [REVIEW])


def test_holm_runs_over_both_claims_of_every_unit_by_hand():
    # 6 claims; sorted: 0.001 < 0.05/6 passes (a earns); 0.02 >= 0.05/5 fails and stops the rest.
    found = verdicts([scored(0.001, 0.999, "a"), scored(0.9, 0.02, "b"), scored(0.3, 0.7, "c")], True, REVIEW,
                     [REVIEW])  # fmt: skip
    assert found == {"a": EARNS, "b": INCONCLUSIVE, "c": INCONCLUSIVE}
    alone = verdicts([scored(0.9, 0.02, "b")], True, REVIEW, [REVIEW])  # 0.02 < 0.05/2 passes
    assert alone == {"b": DROP}


def test_the_holm_step_is_s3_s():
    assert verdict_module.holm is uncertainty.holm


def test_no_verdict_without_review_on_another_day_or_below_30_changed():
    unit = [scored(0.001, 0.999)]
    assert verdicts(unit, False, REVIEW, [REVIEW])["u"].startswith("no verdict: not a scheduled review")
    assert (
        verdicts(unit, True, REVIEW - timedelta(1), [REVIEW])["u"]
        == "no verdict: 2027-06-28 is not a scheduled review date"
    )
    assert verdicts([scored(0.001, 0.999, changed=29)], True, REVIEW, [REVIEW])["u"] == (
        "no verdict: 29 of 30 changed opportunities"
    )
    assert verdicts([scored(0.001, 0.999, changed=30)], True, REVIEW, [REVIEW])["u"] == EARNS


def test_an_unknown_cost_gives_no_verdict_and_stays_in_the_family_with_p_1():
    unknown = UnitScore("x", 40, 40, 10.0, None, None, None, None, None, None, None)
    found = verdicts([unknown, scored(0.9, 0.02, "b")], True, REVIEW, [REVIEW])
    assert found == {"x": COST_UNKNOWN, "b": INCONCLUSIVE}  # 4 claims: b's 0.02 >= 0.05/4 = 0.0125
    assert score_unit("x", opportunities(cost=None)).p_earns is None


def test_the_family_is_fixed_so_an_ineligible_unit_never_moves_another_s_threshold():
    """Units a, b and c are registered; c has 29 changed opportunities at the first review and 30 at the next. With
    the fixed family (6 claims), a's p = 0.009 passes only if 0.009 < 0.05/6 = 0.00833: it fails at both reviews,
    whatever c's eligibility. A family of eligible units only would give a 4-claim threshold of 0.0125 at the first
    review (a passes) and 6 claims at the next (a fails): a's verdict would move with c's sample."""
    a, b = scored(0.009, 0.99, "a"), scored(0.5, 0.5, "b")
    c_first = UnitScore("c", 29, 29, 0.0, 1.0, 0.0, None, 0.4, 0.6, None, None)
    c_next = scored(0.4, 0.6, "c")
    first = verdicts([a, b, c_first], True, REVIEW, [REVIEW])
    later = verdicts([a, b, c_next], True, REVIEW, [REVIEW])
    assert first["a"] == later["a"] == INCONCLUSIVE
    assert first["c"] == "no verdict: 29 of 30 changed opportunities"


def test_the_spread_beside_the_p_values_shows_each_block_s_calendar_span_and_the_months():
    s = score_unit("macro", opportunities())
    assert s.block_spans == ((date(2026, 11, 2), date(2026, 11, 21)), (date(2026, 11, 22), date(2026, 12, 1)))
    assert s.months == (("2026-11", 29), ("2026-12", 1))


def test_earns_and_drop_are_labelled_provisional():
    assert "provisional" in EARNS and "provisional" in DROP and "F9b" in EARNS
