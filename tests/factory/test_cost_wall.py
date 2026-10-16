"""G1, the cost wall (story R1b, criteria 4 and 5): FACTORY_RULES' worked condor example from response 92 l.39-40."""

import pytest

from fno.config import load_app_config
from fno.costs import order_charges, settlement_charges_breakdown
from fno.factory.constants import GrossKind, Outcome
from fno.factory.cost_wall import ASSUMED_HURDLE, NO_STATED_EDGE, ScreenInputs, Tail, screen
from fno.factory.gross import MeasuredGross, NoStatedEdge, StatedGross
from fno.factory.round_trip import Leg, LegsCost, StatedCost
from fno.factory.t_bound import t_quantile

NO_TAIL = Tail(0.0, 0.0, True, None, None)  # a measured history already contains its maximum losses


def condor(mean, sd, n, cost):
    return screen(ScreenInputs(MeasuredGross(mean, sd, n, "response 92"), StatedCost(cost, "response 92"), NO_TAIL))


@pytest.mark.parametrize(
    ("mean", "sd", "n", "cost", "t", "bound", "net", "ratio", "net_on_means"),
    [(978, 2667, 33, 824, 1.3086, 370.5, -453.5, 1.19, 154), (408, 3403, 57, 814, 1.2969, -176.5, -990.5, 0.50, -406)],
)
def test_the_worked_condor_example(mean, sd, n, cost, t, bound, net, ratio, net_on_means):
    assert t_quantile(0.90, n - 1) == pytest.approx(t, abs=5e-5)
    result = condor(mean, sd, n, cost)
    assert result.figures["bound"] == pytest.approx(bound, abs=0.05)
    assert result.figures["net"] == pytest.approx(net, abs=0.05)
    assert result.figures["ratio"] == pytest.approx(ratio, abs=0.005)
    assert mean - cost == net_on_means
    assert result.outcome == Outcome.SCREENED_OUT and result.thin_margin


def test_a_positive_net_on_the_bound_passes_even_with_a_thin_margin():
    result = screen(ScreenInputs(StatedGross(GrossKind.PUBLISHED, 150, "study"), StatedCost(100, "m"), NO_TAIL))
    assert result.outcome == Outcome.PASSED and result.figures["net"] == 50 and result.thin_margin
    zero = screen(ScreenInputs(StatedGross(GrossKind.PUBLISHED, 100, "study"), StatedCost(100, "m"), NO_TAIL))
    assert zero.outcome == Outcome.SCREENED_OUT and zero.figures["net"] == 0  # at zero: screened out
    wide = screen(ScreenInputs(StatedGross(GrossKind.ARITHMETIC, 250, "sum"), StatedCost(100, "m"), NO_TAIL))
    assert wide.outcome == Outcome.PASSED and not wide.thin_margin


@pytest.mark.parametrize(
    ("kind", "reasons"),
    [(GrossKind.NONE, (NO_STATED_EDGE,)), (GrossKind.ASSUMED_HURDLE, (NO_STATED_EDGE, ASSUMED_HURDLE))],
)
def test_no_stated_edge_and_an_assumed_hurdle_never_pass(kind, reasons):
    result = screen(ScreenInputs(NoStatedEdge(kind, "studies disagree"), None, None))
    assert (result.outcome, result.reasons, result.figures) == (Outcome.SCREENED_OUT, reasons, {})


@pytest.mark.parametrize(
    ("tail", "extra"),
    [(Tail(0.1, 9000, True, None, None), 0.0), (Tail(0.1, 9000, False, None, None), 900.0),
     (Tail(0.1, 9000, True, 0.27, "response 94 W5"), 1530.0), (Tail(0.3, 9000, True, 0.27, "W5"), 0.0)],
)  # fmt: skip
def test_the_tail_uses_the_worse_rate_beyond_what_the_gross_contains(tail, extra):
    assert tail.extra_loss() == pytest.approx(extra)


def test_a_legs_cost_is_c1s_charges_plus_the_pads_on_every_order():
    charges = load_app_config()["charges"]
    short = Leg("sell", 65, 120.0, 40.0, None, 1.5, "A4 15:00 quotes")
    long = Leg("buy", 65, 30.0, None, 0.0, 1.0, "A4 15:00 quotes")
    expected_short = order_charges(120.0, 65, "sell", charges) + order_charges(40.0, 65, "buy", charges) + 2 * 1.5 * 65
    expected_long = order_charges(30.0, 65, "buy", charges) + 1.0 * 65  # expired worthless: no exit order, no charge
    assert LegsCost((short, long), charges).rupees() == pytest.approx(expected_short + expected_long)
    exercised = Leg("buy", 65, 30.0, None, 50.0, 1.0, "A4")
    settled = sum(settlement_charges_breakdown(50.0, 65, "sell", charges).values())
    assert exercised.rupees(charges) == pytest.approx(order_charges(30.0, 65, "buy", charges) + 65 + settled)
