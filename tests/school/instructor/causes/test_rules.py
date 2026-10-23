"""Part c's rules (story MS-INS, criteria 1-5 and 7): one plant per cause, each threshold at and just beyond its value,
the winner forms, the frozen precedence, "unclassified" and the modifiers."""

from dataclasses import replace

import pytest

from fno.school.constants import ExitReason
from fno.school.instructor.causes.classify import causes_of, modifier
from fno.school.instructor.causes.evidence import Controls
from fno.school.instructor.causes.rules import verdicts
from fno.school.instructor.causes.terms import Stance
from fno.school.instructor.contracts import Cause, Modifier
from tests.school.instructor.causes.evidence_builders import (
    CONTROLS_BOTH_LOST,
    CONTROLS_BOTH_WON,
    FLAT,
    evidence,
    with_parts,
)

SHORT_VOL = replace(FLAT, short_volatility=True)
LONG_VOL_DEBIT = replace(FLAT, long_volatility=True, long_premium=True)
DIRECTIONAL = replace(FLAT, directional=True)

PLANTS = {
    Cause.MOVE_BEYOND_RANGE: evidence(z=1.7),
    Cause.WRONG_DIRECTION: with_parts(evidence(stance=DIRECTIONAL), delta=-900.0),
    Cause.VOLATILITY_ROSE: with_parts(evidence(stance=SHORT_VOL), vega=-400.0),
    Cause.VOLATILITY_COLLAPSED: with_parts(evidence(stance=LONG_VOL_DEBIT, inside_breakevens=False), vega=-400.0),
    Cause.TIME_DECAY: with_parts(evidence(stance=LONG_VOL_DEBIT, inside_breakevens=True), theta=-400.0),
    Cause.GAP_THROUGH_STOP: evidence(exit_reason=ExitReason.LOSS_LIMIT, stop_rs=700.0),
    Cause.SCHEDULED_EVENT_SHOCK: evidence(z=2.1, event_in_window=True),
    Cause.UNSCHEDULED_SHOCK: evidence(market=(2.1, -2.2, 2.3, 0.1)),
    Cause.COSTS_ATE_EDGE: evidence(gross=0.0),
    Cause.BAD_PRICE_OR_DATA: evidence(data_fault=True),
    Cause.EXIT_WHIPSAW: evidence(exit_reason=ExitReason.PROFIT_TARGET, hold_net=1001.0),
    Cause.NORMAL_NOISE: evidence(noise=(-920.0, 10.0)),  # the mid-to-mid P&L: the net plus 80 of costs
    Cause.RULE_BROKEN: evidence(replay_matches=False),
}


def test_the_neutral_loser_is_unclassified_with_nothing_untestable():
    assert causes_of(evidence()) == (None, (), ())


@pytest.mark.parametrize("cause", list(Cause), ids=str)
def test_each_plant_gives_its_cause_as_primary(cause):
    assert causes_of(PLANTS[cause])[0] == cause


C = Cause
BOUNDARIES = [
    (C.MOVE_BEYOND_RANGE, evidence(z=1.645), False),
    (C.MOVE_BEYOND_RANGE, evidence(z=-1.6451), True),
    (C.SCHEDULED_EVENT_SHOCK, evidence(z=2.0, event_in_window=True), False),
    (C.SCHEDULED_EVENT_SHOCK, evidence(z=2.0001, event_in_window=True), True),
    (C.UNSCHEDULED_SHOCK, evidence(market=(2.1, 2.1, 0.0, 0.0)), False),
    (C.UNSCHEDULED_SHOCK, evidence(market=(2.1, 2.1, -2.1, 0.0)), True),
    (C.UNSCHEDULED_SHOCK, evidence(market=(2.1, 2.1)), None),  # fewer than 3 measurable
    (C.VOLATILITY_ROSE, with_parts(evidence(stance=SHORT_VOL), vega=-399.99), False),
    (C.VOLATILITY_ROSE, with_parts(evidence(stance=SHORT_VOL), vega=-400.0), True),
    (C.GAP_THROUGH_STOP, evidence(exit_reason=ExitReason.LOSS_LIMIT, stop_rs=800.0), False),  # 1.25 x 800 = the loss
    (C.GAP_THROUGH_STOP, evidence(exit_reason=ExitReason.LOSS_LIMIT, stop_rs=799.99), True),
    (C.GAP_THROUGH_STOP, evidence(exit_reason=ExitReason.LOSS_LIMIT), None),  # a card without a stop
    (C.EXIT_WHIPSAW, evidence(exit_reason=ExitReason.LOSS_LIMIT, hold_net=0.0), False),  # better by exactly 1x the loss
    (C.EXIT_WHIPSAW, evidence(exit_reason=ExitReason.LOSS_LIMIT, hold_net=0.01), True),
    (C.EXIT_WHIPSAW, evidence(exit_reason=ExitReason.LOSS_LIMIT), None),  # no settlement yet
    (C.NORMAL_NOISE, evidence(noise=(-910.0, 10.0)), True),  # the mid-to-mid P&L is -920: exactly 1 sd
    (C.NORMAL_NOISE, evidence(noise=(-909.99, 10.0)), False),
    (C.COSTS_ATE_EDGE, evidence(gross=-0.01), False),
    (C.COSTS_ATE_EDGE, evidence(gross=0.0), True),
    (C.WRONG_DIRECTION, with_parts(evidence(stance=DIRECTIONAL), delta=-1.0), True),
    (C.WRONG_DIRECTION, with_parts(evidence(stance=DIRECTIONAL), delta=0.0), False),
]


@pytest.mark.parametrize("cause, ev, expected", BOUNDARIES, ids=lambda v: str(v) if isinstance(v, Cause) else "")
def test_each_threshold_at_and_just_beyond(cause, ev, expected):
    assert verdicts(ev)[cause] is expected


def test_a_winner_reads_the_winner_forms_and_never_the_loser_only_causes():
    win = evidence(net=500.0, gross=600.0, exit_reason=ExitReason.LOSS_LIMIT, stop_rs=1.0)
    assert causes_of(win)[0] is None  # no gap through stop and no costs on a winner
    assert causes_of(with_parts(replace(win, stance=SHORT_VOL), vega=200.0))[0] == Cause.VOLATILITY_ROSE
    assert causes_of(with_parts(replace(win, stance=SHORT_VOL), vega=199.99))[0] is None  # 40% of the gain
    assert causes_of(with_parts(replace(win, stance=DIRECTIONAL), delta=10.0))[0] == Cause.WRONG_DIRECTION
    assert causes_of(with_parts(replace(win, stance=FLAT), theta=200.0))[0] == Cause.TIME_DECAY  # decay earned
    target = replace(win, exit_reason=ExitReason.PROFIT_TARGET, hold_net=1000.01)
    assert causes_of(target)[0] == Cause.EXIT_WHIPSAW and causes_of(replace(target, hold_net=1000.0))[0] is None


def test_a_loser_inside_the_range_only_is_wrong_direction():
    directional = with_parts(evidence(stance=DIRECTIONAL), delta=-900.0)
    assert causes_of(replace(directional, z=1.7))[0] == Cause.MOVE_BEYOND_RANGE
    assert Cause.WRONG_DIRECTION not in causes_of(replace(directional, z=1.7))[1]


def test_time_decay_needs_a_debit_and_the_level_inside_the_breakevens():
    decay = with_parts(evidence(stance=LONG_VOL_DEBIT, inside_breakevens=False), theta=-400.0)
    assert causes_of(decay)[0] is None
    assert Cause.TIME_DECAY in causes_of(replace(decay, inside_breakevens=None))[2]  # not testable


def test_the_precedence_with_four_causes_firing_and_greeks_by_size():
    ev = with_parts(evidence(stance=replace(SHORT_VOL, directional=True), z=1.7, gross=0.0), delta=-500.0, vega=-900.0)
    assert causes_of(ev)[:2] == (Cause.MOVE_BEYOND_RANGE, (Cause.VOLATILITY_ROSE, Cause.COSTS_ATE_EDGE))
    assert causes_of(replace(ev, replay_matches=False))[0] == Cause.RULE_BROKEN  # cause 13 heads the order
    assert causes_of(replace(ev, data_fault=True, replay_matches=False))[1][0] == Cause.BAD_PRICE_OR_DATA


def test_missing_inputs_are_not_testable_never_guessed():
    blank = evidence(
        z=None,
        market=(2.5, 2.5),
        stance=None,
        attribution=None,
        noise=None,
        replay_matches=None,
        exit_reason=ExitReason.PROFIT_TARGET,
        data_fault=True,
    )
    primary, _, untestable = causes_of(blank)
    assert primary == Cause.BAD_PRICE_OR_DATA
    assert set(untestable) == {
        Cause.MOVE_BEYOND_RANGE,
        Cause.WRONG_DIRECTION,
        Cause.VOLATILITY_ROSE,
        Cause.VOLATILITY_COLLAPSED,
        Cause.TIME_DECAY,
        Cause.UNSCHEDULED_SHOCK,
        Cause.EXIT_WHIPSAW,
        Cause.NORMAL_NOISE,
        Cause.RULE_BROKEN,
    }


def test_a_known_event_rules_out_the_unscheduled_shock():
    assert causes_of(evidence(market=(2.5, 2.5, 2.5, 2.5), event_in_window=True))[0] is None


@pytest.mark.parametrize(
    "net, controls, expected",
    [
        (-5.0, CONTROLS_BOTH_LOST, Modifier.HARD_ROAD),
        (5.0, CONTROLS_BOTH_LOST, Modifier.HARD_ROAD),
        (-5.0, CONTROLS_BOTH_WON, Modifier.BAD_DRIVER),
        (5.0, CONTROLS_BOTH_WON, Modifier.NONE),
        (-5.0, Controls(-1.0, 1.0), Modifier.NONE),
        (-5.0, Controls(None, 1.0), Modifier.NOT_TESTABLE),
        (-5.0, None, Modifier.NOT_TESTABLE),
        (-5.0, Controls(0.0, 0.0), Modifier.BAD_DRIVER),
    ],
)
def test_the_modifiers_from_ref_and_rc1_on_the_same_road_slot(net, controls, expected):
    assert modifier(net, controls) == expected


def test_a_stance_is_read_once_for_each_volatility_side():
    assert Stance(True, False, False, False).short_volatility and not FLAT.long_volatility


def test_causes_2_to_5_are_ranked_by_the_size_of_their_component():
    both = evidence(stance=replace(SHORT_VOL, directional=True))
    assert causes_of(with_parts(both, delta=-450.0, vega=-900.0))[:2] == (
        Cause.VOLATILITY_ROSE, (Cause.WRONG_DIRECTION,))  # fmt: skip
    assert causes_of(with_parts(both, delta=-950.0, vega=-900.0))[:2] == (
        Cause.WRONG_DIRECTION, (Cause.VOLATILITY_ROSE,))  # fmt: skip


def test_a_known_answer_is_given_even_when_the_move_is_unknown():
    no_move = evidence(z=None)
    assert verdicts(no_move)[Cause.SCHEDULED_EVENT_SHOCK] is False  # no event in the window: certainly not cause 7
    assert verdicts(replace(no_move, event_in_window=True))[Cause.SCHEDULED_EVENT_SHOCK] is None
    assert verdicts(no_move)[Cause.WRONG_DIRECTION] is False  # not directional: certainly not cause 2
    assert verdicts(replace(no_move, stance=DIRECTIONAL))[Cause.WRONG_DIRECTION] is None


def test_a_flat_result_fires_no_component_cause():
    flat = with_parts(evidence(net=0.0, gross=80.0, stance=SHORT_VOL), vega=10.0, theta=5.0)
    assert not any(verdicts(flat)[c] for c in (Cause.VOLATILITY_ROSE, Cause.TIME_DECAY, Cause.VOLATILITY_COLLAPSED))
    tiny_gain = with_parts(evidence(net=0.01, gross=80.0, stance=SHORT_VOL), vega=10.0)
    assert verdicts(tiny_gain)[Cause.VOLATILITY_ROSE] is True  # any gain, however small, can be explained
