"""Story G6: cumulative Holm over the 15 registered members with p = 1 for every member not judged (ChatGPT review 98),
membership and decision timestamp on every report, and the stop rule's A/B table with zero trials, missing and void
outcomes (design v2 section 8.2)."""

from __future__ import annotations

from datetime import datetime

import pytest

from fno.constants import (
    CONTINUE,
    CONTINUE_HALF_AI_BUDGET,
    STOP_NO,
    STOP_NO_ECONOMIC_TEST,
    STOP_OR_PIVOT,
    STOP_UNDECIDED,
    STOP_YES,
    UNDECIDED_OPTION_1,
    UNDECIDED_OPTION_2,
    V1_RV_1S,
    V3_RV_20S,
    V4_CLAIM,
    V4_FUTILE,
    V4_OPEN,
    V4_SLOT_AI,
    V4_SLOT_HYBRID,
    V4_SLOT_RULES,
    V4_TOO_SMALL,
    V6_BIG_MOVE_1S,
)
from fno.forecast_v4.family import MemberResult, holm, judge_family
from fno.forecast_v4.stop_rule import ShadowResult, forecasting_test, money_test, review_outcome
from fno.forecast_v4.terms import FAMILY, FAMILY_SIZE, LOOK_SETTLE_DATE, LOOK_STOP_REVIEW, family_seed_word
from fno.models import IST

AT = datetime(2027, 5, 31, 18, 0, tzinfo=IST)
V6_RULES, V1_RULES = (V6_BIG_MOVE_1S, V4_SLOT_RULES), (V1_RV_1S, V4_SLOT_RULES)


def test_the_family_is_fixed_at_fifteen_members_in_a_numbered_order():
    assert FAMILY_SIZE == 15 and len(set(FAMILY)) == 15
    assert family_seed_word(V1_RV_1S, V4_SLOT_RULES) == 1 and family_seed_word(*FAMILY[-1]) == 15
    assert not any(q == V3_RV_20S for q, _ in FAMILY)  # 20-session questions are reported, never members


def test_holm_step_down_matches_hand_thresholds():
    assert holm([0.01, 0.04, 0.03, 0.005], 0.05) == [True, False, False, True]  # 0.005<=.0125, .01<=.0167, .03>.025
    assert holm([0.01, 0.02, 0.03, 0.04], 0.04) == [True, False, False, False]  # 0.02 > 0.04 / 3
    assert holm([0.01, 0.02, 0.03, 0.04], 0.16) == [True, True, True, True]


def test_unjudged_members_enter_holm_at_p_one_so_the_first_step_is_rate_over_fifteen():
    # Alone, p = 0.002 would pass; in the family of 15 at look 1 (0.02 / 15 = 0.00133) it does not.
    decision = judge_family(LOOK_STOP_REVIEW, AT, {V6_RULES: MemberResult(0.002, True, False)})
    v6 = next(m for m in decision.members if (m.question, m.slot) == V6_RULES)
    assert not v6.holm_significant and v6.verdict == V4_OPEN
    assert sum(m.judged for m in decision.members) == 1
    assert all(m.p_used == 1.0 for m in decision.members if not m.judged)
    passed = judge_family(LOOK_STOP_REVIEW, AT, {V6_RULES: MemberResult(0.0013, True, False)})
    assert next(m for m in passed.members if (m.question, m.slot) == V6_RULES).verdict == V4_CLAIM


def test_a_member_with_p_none_is_not_judged_and_counts_at_p_one():
    decision = judge_family(LOOK_SETTLE_DATE, AT, {V1_RULES: MemberResult(None, False, False)})
    v1 = next(m for m in decision.members if (m.question, m.slot) == V1_RULES)
    assert (v1.judged, v1.p_used, v1.verdict) == (False, 1.0, V4_OPEN)
    assert decision.error_rate == 0.03


def test_significant_but_below_the_minimum_effect_is_real_but_too_small_and_futility_is_reported():
    results = {V6_RULES: MemberResult(0.0001, False, False), V1_RULES: MemberResult(0.6, False, True)}
    verdicts = {(m.question, m.slot): m.verdict for m in judge_family(LOOK_STOP_REVIEW, AT, results).members}
    assert verdicts[V6_RULES] == V4_TOO_SMALL and verdicts[V1_RULES] == V4_FUTILE


def test_every_report_states_all_members_the_look_its_rate_and_the_decision_timestamp():
    lines = judge_family(LOOK_STOP_REVIEW, AT, {V6_RULES: MemberResult(0.3, False, False)}).lines()
    assert lines[0] == (
        "protocol v4 family: 15 members, 1 judged, 14 at p = 1; look stop_rule_review at family-wise 0.02; "
        "decided at 2027-05-31T18:00:00+05:30"
    )
    assert len(lines) == 16 and sum("(not judged)" in line for line in lines) == 14


def test_a_decision_needs_a_time_zone_and_only_registered_members():
    with pytest.raises(ValueError, match="time zone"):
        judge_family(LOOK_STOP_REVIEW, datetime(2027, 5, 31), {})
    with pytest.raises(ValueError, match="not members"):
        judge_family(LOOK_STOP_REVIEW, AT, {(V3_RV_20S, V4_SLOT_RULES): MemberResult(0.01, True, False)})


def _members(results):
    return judge_family(LOOK_STOP_REVIEW, AT, results).members


def test_a_with_zero_registered_forecasters_is_undecided_never_no():
    assert forecasting_test(_members({}), registered=set()) == STOP_UNDECIDED


def test_a_is_no_only_when_every_counted_member_is_futile():
    registered = {V6_RULES, V1_RULES}
    both = {V6_RULES: MemberResult(0.7, False, True), V1_RULES: MemberResult(0.8, False, True)}
    assert forecasting_test(_members(both), registered) == STOP_NO
    one_open = {V6_RULES: MemberResult(0.7, False, True), V1_RULES: MemberResult(None, False, False)}
    assert forecasting_test(_members(one_open), registered) == STOP_UNDECIDED  # V1 has under 2L pairs (missing, void)


def test_a_counts_a_significant_but_too_small_member_as_futile_when_its_bound_is_below_the_effect():
    results = {V6_RULES: MemberResult(0.0001, False, True), V1_RULES: MemberResult(0.9, False, True)}
    members = _members(results)
    assert {m.verdict for m in members if m.judged} == {V4_TOO_SMALL, V4_FUTILE}
    assert forecasting_test(members, {V6_RULES, V1_RULES}) == STOP_NO


def test_a_is_yes_on_one_claim_and_unregistered_slots_are_not_counted():
    results = {V6_RULES: MemberResult(0.0001, True, False)}
    assert forecasting_test(_members(results), {V6_RULES}) == STOP_YES
    hybrid = (V6_BIG_MOVE_1S, V4_SLOT_HYBRID)
    assert forecasting_test(_members(results), {hybrid}) == STOP_UNDECIDED


def test_b_with_zero_shadows_is_no_economic_test():
    assert money_test([]) == STOP_NO_ECONOMIC_TEST


def test_b_three_results():
    reached_below = ShadowResult(-300.0, 40.0, True, 100.0)
    assert money_test([reached_below]) == STOP_NO
    assert money_test([reached_below, ShadowResult(12.0, 900.0, True, 100.0)]) == STOP_YES
    assert money_test([reached_below, ShadowResult(-500.0, 40.0, False, 100.0)]) == STOP_UNDECIDED  # sample not reached
    assert money_test([ShadowResult(None, None, False, 100.0)]) == STOP_UNDECIDED  # no resolved trade: no bound


@pytest.mark.parametrize(
    ("a", "b", "years", "expected"),
    [
        (STOP_NO, STOP_NO, None, STOP_OR_PIVOT),
        (STOP_YES, STOP_NO, None, CONTINUE_HALF_AI_BUDGET),
        (STOP_YES, STOP_NO_ECONOMIC_TEST, None, CONTINUE_HALF_AI_BUDGET),
        (STOP_YES, STOP_UNDECIDED, None, CONTINUE_HALF_AI_BUDGET),
        (STOP_NO, STOP_YES, None, CONTINUE),
        (STOP_UNDECIDED, STOP_YES, None, CONTINUE),
        (STOP_NO, STOP_NO_ECONOMIC_TEST, 1.5, UNDECIDED_OPTION_1),  # zero shadows never stops the project
        (STOP_UNDECIDED, STOP_NO, 2.0, UNDECIDED_OPTION_1),
        (STOP_UNDECIDED, STOP_UNDECIDED, 2.01, UNDECIDED_OPTION_2),
        (STOP_UNDECIDED, STOP_NO_ECONOMIC_TEST, None, UNDECIDED_OPTION_2),  # nothing reached its power report
    ],
)
def test_the_review_table(a, b, years, expected):
    assert review_outcome(a, b, years) == expected


def test_slots_are_rules_hybrid_and_ai_team():
    assert {slot for _, slot in FAMILY} == {V4_SLOT_RULES, V4_SLOT_HYBRID, V4_SLOT_AI}
