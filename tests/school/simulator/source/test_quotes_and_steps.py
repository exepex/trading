"""The quote arithmetic and the strike step (MS-SIM-c)."""

import pytest

from fno.school.simulator.constants import SIZE_GATE_WAIVED
from fno.school.simulator.source.quotes import no_quote, point_quote, practice_quote
from fno.school.simulator.source.steps import strike_step


def test_the_bid_rounds_down_and_the_ask_up_to_the_tick():
    quote = practice_quote(100.0, 0.0123)  # half = 1.23
    assert (quote.bid, quote.ask) == (98.75, 101.25) and quote.last == 100.0


def test_the_bid_floors_rather_than_rounds_to_nearest():
    quote = practice_quote(100.0, 0.0122)  # bid 98.78: down to 98.75, not nearest 98.80
    assert quote.bid == 98.75


def test_float_noise_on_a_tick_edge_does_not_cost_a_tick():
    quote = practice_quote(7.5, 0.02)  # (7.5 - 0.15) / 0.05 is 146.99999999999997 in floating point
    assert quote.bid == 7.35


def test_a_quote_on_a_tick_edge_is_not_widened_by_float_noise():
    quote = practice_quote(100.0, 0.01)  # half = 1.00 exactly
    assert (quote.bid, quote.ask) == (99.0, 101.0)


def test_the_half_is_floored_at_half_a_tick():
    quote = practice_quote(10.0, 0.0)
    assert (quote.bid, quote.ask) == (9.95, 10.05)


def test_a_bid_that_would_be_zero_or_negative_is_no_bid():
    assert practice_quote(1.0, 2.0).bid is None  # 1 - 2 is below zero
    assert practice_quote(0.05, 0.0).bid is None
    assert not practice_quote(1.0, 2.0).two_sided


def test_the_sizes_are_the_waiver_switch_and_a_point_quote_has_no_width():
    assert practice_quote(100.0, 0.01).bid_qty == SIZE_GATE_WAIVED == practice_quote(100.0, 0.01).ask_qty
    point = point_quote(7.5)
    assert point.bid == point.ask == 7.5 and point.valid


def test_a_leg_with_no_price_is_an_invalid_quote():
    quote = no_quote(12.0)
    assert not quote.valid and not quote.two_sided and quote.last == 12.0


def test_the_step_is_the_most_common_gap_near_the_money():
    strikes = [16800, 16900, 17000, 17100, 17200, 17250, 17300]  # one 50 gap among 100 gaps
    assert strike_step(strikes, 17000.0) == 100.0


def test_far_strikes_listed_more_sparsely_do_not_decide_the_step():
    near = [17000 + 50 * n for n in range(-4, 5)]
    far = [15000 + 100 * n for n in range(10)]  # a denser far grid would win a count over the whole listing
    assert strike_step(near + far, 17000.0) == 50.0


def test_the_step_of_one_strike_is_unknown_and_a_tie_takes_the_smaller_gap():
    assert strike_step([17000], 17000.0) is None and strike_step([], 17000.0) is None
    assert strike_step([100, 150, 250], 150.0) == 50.0


@pytest.mark.parametrize("strikes", [[17000, 17000]])
def test_duplicate_strikes_are_one_strike(strikes):
    assert strike_step(strikes, 17000.0) is None
