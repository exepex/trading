"""Story G8 criteria 4-7: both gates at their boundaries, the threshold calls, closed members, the family output with
every member's regime line, and Test A."""

from datetime import datetime, timedelta, timezone

import pytest

from fno.constants import V6_BIG_MOVE_5S, V7_VIX_UP_5S
from fno.forecast_scoring.v4.comparison import compare, paired_rows
from fno.forecast_scoring.v4.look import NO_WINDOW, member_result, run_look
from fno.forecast_scoring.v4.thresholds import Thresholds, ThresholdSource
from fno.forecast_v4.stop_rule import forecasting_test
from fno.forecast_v4.terms import FAMILY, LOOK_SETTLE_DATE, LOOK_STOP_REVIEW
from tests.forecast_scoring_v4.helpers import synthetic_window, values

IST = timezone(timedelta(hours=5, minutes=30))
AT = datetime(2027, 5, 31, 16, 0, tzinfo=IST)


class Recording(ThresholdSource):
    def __init__(self, claim=0.5, futility=0.5):
        self.calls, self.claim, self.futility = [], claim, futility

    def thresholds(self, question, look, claim_n, futility_n, band):
        self.calls.append((question, look, claim_n, futility_n, band))
        return Thresholds(self.claim, self.futility)


def v6b(n: int, big_days: int, forecast: float = 0.3):
    days, outcomes = synthetic_window(n, big_days)
    rows = paired_rows(values({d: forecast for d in days}), values({d: 0.1376 for d in days}), outcomes)
    return compare(V6_BIG_MOVE_5S, "weather_m1", "base_rate", rows, outcomes, 4)


@pytest.mark.parametrize(("n", "big", "judged"), [(125, 4, False), (125, 5, True), (125, 12, True),
                                                 (125, 13, False), (250, 25, True), (250, 26, False)])  # fmt: skip
def test_both_gates_at_their_boundaries(n, big, judged):
    source = Recording()
    result = member_result(v6b(n, big), LOOK_STOP_REVIEW, source, 4)
    assert (result.p_value is not None) == judged and bool(source.calls) == judged


def test_thresholds_are_asked_with_the_scored_n_the_gate_n_the_look_and_the_band():
    source = Recording()
    member_result(v6b(125, 9), LOOK_SETTLE_DATE, source, 4)
    assert source.calls == [(V6_BIG_MOVE_5S, LOOK_SETTLE_DATE, 125, 125, (8, 12))]


def test_fewer_than_12_batches_is_not_judged():
    source = Recording()
    assert member_result(v6b(119, 9), LOOK_STOP_REVIEW, source, 4).p_value is None and not source.calls


def test_the_family_lists_all_15_members_with_their_regime_lines_and_test_a():
    member = (V6_BIG_MOVE_5S, "rules")
    look = run_look(LOOK_STOP_REVIEW, AT, {member: v6b(125, 9)}, Recording(claim=1.0, futility=0.0), set())
    lines = look.lines()
    assert lines[0].startswith("protocol v4 family: 15 members, 1 judged, 14 at p = 1; look stop_rule_review at "
                               "family-wise 0.02; decided at 2027-05-31T16:00:00+05:30")  # fmt: skip
    assert len(lines) == 1 + 2 * len(FAMILY) + 1 + 1  # one miss line for the member with a comparison
    position = 1 + 2 * FAMILY.index(member)
    assert lines[position + 1] == "  scored window regime: mean India VIX 15.0, 9 2% days, band 8-12"
    assert lines[position + 2] == "  misses: 0 of 125 baseline days (0.0%), 0 of 9 2% days; input failures: 0"
    assert lines[2] == f"  {NO_WINDOW}" and lines[-1] == f"Test A (forecasting): {look.test_a}"
    assert look.test_a == forecasting_test(look.decision.members, {member})


def test_no_registered_member_gives_undecided_and_v7_stays_at_p_1():
    look = run_look(LOOK_STOP_REVIEW, AT, {(V7_VIX_UP_5S, "rules"): v6b(125, 9)}, Recording(), set())
    assert look.test_a == "undecided"
    v7 = next(m for m in look.decision.members if m.question == V7_VIX_UP_5S and m.slot == "rules")
    assert not v7.judged and v7.p_used == 1.0


def test_a_member_closed_at_look_1_is_not_judged_at_look_2():
    member, source = (V6_BIG_MOVE_5S, "rules"), Recording()
    look = run_look(LOOK_SETTLE_DATE, AT, {member: v6b(125, 9)}, source, {member})
    assert not source.calls and not look.decision.members[FAMILY.index(member)].judged


def test_a_point_member_asks_futility_with_the_gate_sets_own_n():
    from fno.constants import V1_RV_1S
    from fno.forecast_scoring.v4.inputs import Outcome

    days, outcomes = synthetic_window(125, 9)
    outcomes = {d: Outcome(0.0 if i < 10 else 1e-4, False, o.vix, o.log_return) for i, (d, o) in
                enumerate(outcomes.items())}  # fmt: skip
    rows = paired_rows(values({d: 2e-4 for d in days}), values({d: 1.5e-4 for d in days}), outcomes)
    source = Recording()
    member_result(compare(V1_RV_1S, "v1_close_blend", "har_daily", rows, outcomes, 1), LOOK_STOP_REVIEW, source, 1)
    assert source.calls == [(V1_RV_1S, LOOK_STOP_REVIEW, 125, 115, (8, 12))]  # 10 zero-RV days left out of the gate


class Refusing(ThresholdSource):
    def thresholds(self, question, look, claim_n, futility_n, band):
        raise AssertionError(f"thresholds asked for {question}")


def test_a_registered_v7_member_is_not_judged_and_never_asks_for_thresholds():
    days, outcomes = synthetic_window(125, 9)
    rows = paired_rows(values({d: 0.3 for d in days}), values({d: 0.5 for d in days}), outcomes)
    v7 = compare(V7_VIX_UP_5S, "v7_rule", "base_rate", rows, outcomes, 13)
    look = run_look(LOOK_STOP_REVIEW, AT, {(V7_VIX_UP_5S, "rules"): v7}, Refusing(), set())
    member = look.decision.members[FAMILY.index((V7_VIX_UP_5S, "rules"))]
    assert not member.judged and member.p_used == 1.0 and look.test_a == "undecided"


def test_a_member_with_too_many_misses_is_operations_undecided_and_keeps_test_a_undecided():
    days, outcomes = synthetic_window(140, 9)
    own = {d: (None if i in range(130, 140) or i == 3 else 0.3) for i, d in enumerate(days)}  # day 3 is a 2% day
    rows = paired_rows(values(own), values({d: 0.1376 for d in days}), outcomes)
    member, source = (V6_BIG_MOVE_5S, "rules"), Recording(claim=1.0, futility=0.0)
    comparison = compare(V6_BIG_MOVE_5S, "weather_m1", "base_rate", rows, outcomes, 4)
    look = run_look(LOOK_STOP_REVIEW, AT, {member: comparison}, source, set())
    verdict = look.decision.members[FAMILY.index(member)]
    assert comparison.misses.big_missed == 1 and comparison.misses.operations_undecided
    assert not source.calls and not verdict.judged and not verdict.futile and look.test_a == "undecided"
    assert any(line.endswith("undecided, operations") for line in look.lines())
