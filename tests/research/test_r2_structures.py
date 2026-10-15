"""R2 structures, cap fit, liquidity and expected net (PROTOCOL.md sections 5-6)."""

from datetime import date

import pytest
from r2_synthetic import CHARGES, NO_CHARGES, flat_chain, quoted
from r2study import structures as st
from r2study.bhav import Leg
from r2study.evaluate import EventMarket, evaluate
from r2study.spreads import SpreadModel
from r2study.structures import STRUCTURES, Strikes, atm_strikes, maximum_loss, price_structure, round_trip_charges

from fno.constants import SIDES
from fno.costs import order_charges

BY_NAME = {s.name[:2]: s for s in STRUCTURES}
STRIKES = Strikes(1000.0, 20.0, 20.0)


def test_k0_is_the_nearest_listed_strike_with_ties_to_the_higher_and_steps_to_its_neighbours():
    chain = flat_chain([960, 1000, 1020, 1050])
    assert atm_strikes(chain, 1009.0) == Strikes(1000.0, 20.0, 40.0)
    assert atm_strikes(chain, 1010.0).k0 == 1020.0  # tie: the higher
    assert atm_strikes(chain, 2000.0) == Strikes(1050.0, None, 30.0)
    assert atm_strikes({}, 1000.0) is None


def test_two_steps_are_twice_the_step_in_that_direction_and_none_without_a_neighbour():
    assert STRIKES.strike(2) == 1040.0 and STRIKES.strike(-2) == 960.0 and STRIKES.strike(0) == 1000.0
    assert Strikes(1000.0, None, 20.0).strike(1) is None


def chain_of(prices: dict) -> dict:
    return {key: Leg(close, 500.0, 1_000_000.0) for key, close in prices.items()}


def test_debit_spread_at_or_above_its_width_is_untradable_and_just_below_is_fine():
    at_width = chain_of({(1000.0, "CE"): 25.0, (1020.0, "CE"): 5.0})
    assert price_structure(BY_NAME["S5"], at_width, STRIKES).untradable == st.DEBIT_AT_WIDTH
    below = chain_of({(1000.0, "CE"): 24.9, (1020.0, "CE"): 5.0})
    priced = price_structure(BY_NAME["S5"], below, STRIKES)
    assert priced.untradable == "" and priced.price == pytest.approx(19.9) and priced.width == 20.0


def test_missing_strike_zero_close_and_no_trades_make_a_structure_untradable():
    assert price_structure(BY_NAME["S1"], {}, STRIKES).untradable == st.NO_STRIKE
    zero = {(1000.0, "CE"): Leg(0.0, 500.0, 1e6)}
    assert price_structure(BY_NAME["S1"], zero, STRIKES).untradable == st.UNPRICED
    idle = {(1000.0, "CE"): Leg(10.0, 0.0, 1e6)}
    assert price_structure(BY_NAME["S1"], idle, STRIKES).untradable == st.UNPRICED


def test_iron_condor_credit_width_and_maximum_loss():
    prices = {(1020.0, "CE"): 12.0, (1040.0, "CE"): 5.0, (980.0, "PE"): 11.0, (960.0, "PE"): 4.0}
    priced = price_structure(BY_NAME["S7"], chain_of(prices), STRIKES)
    assert priced.price == pytest.approx(14.0) and priced.width == 20.0
    assert maximum_loss(priced, 100, 50.0) == pytest.approx((20.0 - 14.0) * 100 + 50.0)
    inverted = {(1020.0, "CE"): 5.0, (1040.0, "CE"): 12.0, (980.0, "PE"): 4.0, (960.0, "PE"): 11.0}
    assert price_structure(BY_NAME["S7"], chain_of(inverted), STRIKES).untradable == st.NOT_POSITIVE


def test_round_trip_charges_are_c1_on_entry_and_exit_at_the_entry_price():
    priced = price_structure(BY_NAME["S5"], chain_of({(1000.0, "CE"): 20.0, (1020.0, "CE"): 8.0}), STRIKES)
    expected = sum(order_charges(p, 100, side, CHARGES) for p in (20.0, 8.0) for side in SIDES)
    assert round_trip_charges(priced, 100, CHARGES) == pytest.approx(expected)
    assert round_trip_charges(priced, 100, NO_CHARGES) == 0.0


def market(contracts=100.0, exit_contracts=100.0, oi=10_000.0, lot=100, close=20.0, previous_contracts=100.0):
    strikes = [960, 980, 1000, 1020, 1040]
    return EventMarket(
        symbol="ABC", reaction=date(2024, 10, 16), sector="IT", lot=lot, strikes=STRIKES,
        entry=flat_chain(strikes, close, contracts, oi), exit=flat_chain(strikes, close, exit_contracts, oi),
        previous=flat_chain(strikes, close, previous_contracts, oi),
    )  # fmt: skip


@pytest.mark.parametrize(
    ("kwargs", "liquid"),
    [
        ({"contracts": 50.0}, True),  # at the limit
        ({"contracts": 49.0}, False),  # just under, entry
        ({"exit_contracts": 49.0}, False),  # just under, exit
        ({"oi": 100 * 100.0}, True),  # 100 contracts of open interest at lot 100
        ({"oi": 100 * 100.0 - 1}, False),
    ],
)
def test_every_leg_needs_50_contracts_on_entry_and_exit_and_100_open_interest(kwargs, liquid):
    assert evaluate(BY_NAME["S1"], market(**kwargs), NO_CHARGES, None).liquid is liquid


def test_cap_boundary_is_at_most_rs_10000():
    at_cap = evaluate(BY_NAME["S1"], market(close=100.0, lot=100), NO_CHARGES, None)
    assert at_cap.fits_without_pads  # 100 x 100 = 10,000 exactly
    over = evaluate(BY_NAME["S1"], market(close=100.01, lot=100), NO_CHARGES, None)
    assert not over.fits_without_pads


def spread_model(spread=0.02, two_sided=True):
    legs = [quoted(steps, c, spread=spread, two_sided=two_sided) for steps in (0, 1, 2, 3) for c in range(60)]
    return SpreadModel(legs)


def test_expected_net_is_hurdle_times_notional_less_charges_and_pads_with_break_even_edge():
    outcome = evaluate(BY_NAME["S1"], market(close=20.0), NO_CHARGES, spread_model(0.02))
    notional = 20.0 * 100
    pads = 2 * 0.02 * 20.0 * 100
    assert outcome.pads == pytest.approx(pads)
    assert outcome.expected_net == pytest.approx(0.05 * notional - pads)
    assert outcome.break_even_edge == pytest.approx(pads / notional)
    assert outcome.counts_for_clusters


def test_condor_tail_term_is_two_percent_of_its_maximum_loss():
    m = market(close=10.0)
    m = EventMarket(**{**m.__dict__, "entry": {**m.entry, (1020.0, "CE"): Leg(12.0, 100.0, 1e6),
                                                 (980.0, "PE"): Leg(11.0, 100.0, 1e6)}})  # fmt: skip
    outcome = evaluate(BY_NAME["S7"], m, NO_CHARGES, spread_model(0.0))
    credit = 12.0 - 10.0 + 11.0 - 10.0
    loss = (20.0 - credit) * 100
    assert outcome.expected_net == pytest.approx(0.05 * credit * 100 - 0.02 * loss)


def test_a_leg_in_an_untradable_bucket_is_not_liquid_at_stage_3():
    outcome = evaluate(BY_NAME["S1"], market(), NO_CHARGES, spread_model(two_sided=False))
    assert outcome.bucket_untradable and not outcome.stage3 and outcome.expected_net is None


def test_condor_credit_at_or_above_the_wider_wing_is_untradable():
    prices = {(1020.0, "CE"): 30.0, (1040.0, "CE"): 5.0, (980.0, "PE"): 0.5, (960.0, "PE"): 5.5}  # credit 20 = wing
    assert price_structure(BY_NAME["S7"], chain_of(prices), STRIKES).untradable == st.DEBIT_AT_WIDTH


def test_condor_maximum_loss_uses_the_wider_wing_when_steps_differ():
    strikes = Strikes(1000.0, 20.0, 50.0)  # 20 up, 50 down (a strike-grid change at K0)
    prices = {(1020.0, "CE"): 12.0, (1040.0, "CE"): 5.0, (950.0, "PE"): 11.0, (900.0, "PE"): 4.0}
    priced = price_structure(BY_NAME["S7"], chain_of(prices), strikes)
    assert priced.width == 50.0 and maximum_loss(priced, 100, 0.0) == pytest.approx((50.0 - 14.0) * 100)


def test_cap_with_pads_is_at_most_rs_10000():
    model = spread_model(0.0)  # zero half-spread: the padded loss equals the debit
    assert evaluate(BY_NAME["S1"], market(close=100.0), NO_CHARGES, model).fits_with_pads
    assert not evaluate(BY_NAME["S1"], market(close=100.0001), NO_CHARGES, model).fits_with_pads


def test_condor_tail_is_two_percent_of_the_maximum_loss_including_costs():
    m = market(close=10.0)
    m = EventMarket(**{**m.__dict__, "entry": {**m.entry, (1020.0, "CE"): Leg(12.0, 100.0, 1e6),
                                                 (980.0, "PE"): Leg(11.0, 100.0, 1e6)}})  # fmt: skip
    outcome = evaluate(BY_NAME["S7"], m, CHARGES, spread_model(0.0))
    credit, costs = 12.0 - 10.0 + 11.0 - 10.0, outcome.charges
    loss = (20.0 - credit) * 100 + costs
    assert costs > 0 and outcome.expected_net == pytest.approx(0.05 * credit * 100 - costs - 0.02 * loss)
