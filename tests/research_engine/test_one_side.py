"""Story STR1 criteria 1-3: the one- and two-leg structures build their legs from the ATM strike, a naked short leg can
never be built or priced, and payoff bounds cover the whole index range while four-leg results stay unchanged."""

import math

import pytest

from fno.composition import build_structures, build_tradable_structures
from fno.constants import OPTION_CALL as CE
from fno.constants import OPTION_PUT as PE
from fno.research_engine.cycle_costs import CycleTerms, PositionCosts
from fno.research_engine.structures import (
    BOUGHT,
    SOLD,
    Leg,
    NakedShortLeg,
    Structure,
    payoff_bounds,
    terminal_value,
)
from tests.risk.builders import CHARGES

STRIKES = [23700.0 + 50 * i for i in range(13)]  # 23,700 to 24,300
SPOT = 24025.0  # halfway between 24,000 and 24,050: the ATM tie takes 24,000
BY_CODE = {s.code: s for s in build_tradable_structures()}


def chain(strikes=STRIKES):
    return frozenset((k, kind) for k in strikes for kind in (CE, PE))


def shown(legs):
    return [(leg.strike, leg.kind, leg.side) for leg in legs]


EXPECTED = {
    ("LC", 0): [(24000, CE, BOUGHT)],
    ("LC", 150): [(24150, CE, BOUGHT)],
    ("LP", 0): [(24000, PE, BOUGHT)],
    ("LP", 150): [(23850, PE, BOUGHT)],
    ("CDS", 200): [(24000, CE, BOUGHT), (24200, CE, SOLD)],
    ("CCS", 200): [(24000, CE, SOLD), (24200, CE, BOUGHT)],
    ("PDS", 200): [(24000, PE, BOUGHT), (23800, PE, SOLD)],
    ("PCS", 200): [(24000, PE, SOLD), (23800, PE, BOUGHT)],
}


@pytest.mark.parametrize(("code", "width"), sorted(EXPECTED))
def test_each_code_builds_its_legs_from_the_atm_strike(code, width):
    assert shown(BY_CODE[code].legs(chain(), SPOT, width)) == EXPECTED[(code, width)]


def test_tradable_structures_are_experiment_1s_three_then_the_six_new_ones():
    assert [s.code for s in build_structures()] == ["SF", "SC", "BF"]
    assert list(BY_CODE) == ["SF", "SC", "BF", "LC", "LP", "CDS", "CCS", "PDS", "PCS"]


@pytest.mark.parametrize("width", [100.0, 200.0, 300.0])
def test_the_iron_flies_are_two_verticals_at_the_same_width(width):
    def legs(*codes):
        return sorted(leg for code in codes for leg in shown(BY_CODE[code].legs(chain(), SPOT, width)))

    assert legs("SF") == legs("CCS", "PCS")
    assert legs("BF") == legs("CDS", "PDS")


@pytest.mark.parametrize("code", ["LC", "LP", "CDS", "CCS", "PDS", "PCS"])
def test_a_leg_not_listed_makes_the_width_unavailable(code):
    assert BY_CODE[code].legs(chain([24000.0]), SPOT, 300) is None
    assert BY_CODE[code].legs(frozenset(), SPOT, 300) is None


@pytest.mark.parametrize(("code", "width"), [("LC", -50), ("LP", -50), ("CDS", 0), ("PCS", 0), ("CCS", -100)])
def test_a_width_that_puts_a_leg_in_the_money_or_cancels_the_legs_is_refused(code, width):
    with pytest.raises(ValueError, match="width"):
        BY_CODE[code].legs(chain(), SPOT, width)


class Planted(Structure):
    """A structure whose `build` returns whatever legs it is given: a code bug or a hostile change."""

    code = "XX"

    def __init__(self, legs):
        self.planted = legs

    def build(self, strikes, spot, width):
        return list(self.planted)


NAKED = {
    "short call": [Leg(24000, CE, SOLD)],
    "short put": [Leg(24000, PE, SOLD)],
    "short call over a bought put": [Leg(24000, CE, SOLD), Leg(23800, PE, BOUGHT)],
    "ratio call spread": [Leg(24000, CE, BOUGHT), Leg(24200, CE, SOLD), Leg(24300, CE, SOLD)],
    "condor missing a put wing": [Leg(24200, CE, SOLD), Leg(23800, PE, SOLD), Leg(24300, CE, BOUGHT)],
}


@pytest.mark.parametrize("name", sorted(NAKED))
def test_no_structure_can_return_a_naked_short_leg(name):
    with pytest.raises(NakedShortLeg):
        Planted(NAKED[name]).legs(chain(), SPOT, 100)


@pytest.mark.parametrize("name", sorted(NAKED))
def test_the_cost_model_refuses_to_price_a_naked_short_leg(name):
    legs = NAKED[name]
    with pytest.raises(NakedShortLeg):
        PositionCosts(CycleTerms(lot=65, charges=CHARGES)).max_loss(legs, [100.0] * len(legs))


def test_a_bought_call_can_be_worth_without_limit_and_a_bought_put_up_to_its_strike():
    assert payoff_bounds([Leg(24000, CE, BOUGHT)]) == (0.0, math.inf)
    assert payoff_bounds([Leg(24000, PE, BOUGHT)]) == (0.0, 24000.0)


@pytest.mark.parametrize(
    ("code", "bounds"), [("CDS", (0.0, 200.0)), ("CCS", (-200.0, 0.0)), ("PDS", (0.0, 200.0)), ("PCS", (-200.0, 0.0))]
)
def test_a_vertical_is_worth_between_zero_and_its_width(code, bounds):
    assert payoff_bounds(BY_CODE[code].legs(chain(), SPOT, 200)) == bounds


@pytest.mark.parametrize("code", ["SF", "SC", "BF"])
@pytest.mark.parametrize("width", [100.0, 150.0, 200.0, 250.0, 300.0])
def test_four_leg_bounds_are_the_strikes_only_values_as_before(code, width):
    strikes = [22000.0 + 50 * i for i in range(81)]
    legs = BY_CODE[code].legs(chain(strikes), 24010.0, width)
    at_strikes = [terminal_value(legs, leg.strike) for leg in legs]  # the formula before STR1
    assert payoff_bounds(legs) == (min(at_strikes), max(at_strikes))


@pytest.mark.parametrize(("code", "debit"), [("LC", 120.0), ("LP", 95.0)])
def test_a_bought_options_maximum_loss_is_its_debit_plus_costs(code, debit):
    legs = BY_CODE[code].legs(chain(), SPOT, 0)
    costs = PositionCosts(CycleTerms(lot=65, charges=CHARGES))
    expected = (debit + 1.0) * 65 + costs.charges(legs, [debit], True) + 65 + costs.charges(legs, [0.0], False)
    assert costs.max_loss(legs, [debit]) == pytest.approx(expected)
