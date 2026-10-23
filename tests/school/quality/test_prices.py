"""EDGE1's impossible-price rule read off a chain of two-sided quotes (story 3.5)."""

import sys
from dataclasses import replace
from pathlib import Path

import pytest

from fno.school.constants import OptionKind, RoadCode
from fno.school.contracts.snapshot import SlotQuote
from fno.school.quality.prices import impossible_keys
from fno.school.roads.capture import CaptureReader
from tests.school.contracts import builders as b
from tests.school.roads.capture_builder import SESSION, DictStore, Plant, road

CALL, PUT = OptionKind.CALL, OptionKind.PUT


def snapshot_of(quotes: dict):
    """A chain of just these quotes, {(strike, kind): (bid, ask)}, at the contracts' fixture spot of 1050."""
    return b.snapshot(quotes={b.key(strike, kind): b.quote(bid, ask) for (strike, kind), (bid, ask) in quotes.items()})


def flagged(quotes: dict) -> set:
    return {(k.strike, k.kind) for k in impossible_keys(snapshot_of(quotes))}


def test_a_clean_recorded_shaped_chain_has_no_impossible_leg():
    store = DictStore()
    bank = road(RoadCode.BANKNIFTY_MONTHLY)
    Plant(bank).write(store)
    assert impossible_keys(CaptureReader({bank.dataset: store}).read(bank, SESSION).snapshot()) == frozenset()


def test_a_call_vertical_worth_more_than_its_width_flags_both_legs():
    assert flagged({(900.0, CALL): (300.0, 301.0), (1000.0, CALL): (100.0, 101.0)}) == {(900.0, CALL), (1000.0, CALL)}


def test_a_dearer_higher_strike_call_is_impossible_when_the_spreads_do_not_overlap():
    assert flagged({(900.0, CALL): (80.0, 81.0), (1000.0, CALL): (100.0, 101.0)}) == {(900.0, CALL), (1000.0, CALL)}


def test_a_put_vertical_is_judged_with_the_higher_strike_as_the_dearer_leg():
    assert flagged({(900.0, PUT): (50.0, 51.0), (1000.0, PUT): (20.0, 21.0)}) == {(900.0, PUT), (1000.0, PUT)}
    assert flagged({(900.0, PUT): (20.0, 21.0), (1000.0, PUT): (60.0, 61.0)}) == set()


def test_overlapping_spreads_are_not_impossible_which_a_mid_only_rule_would_call_so():
    quotes = {(900.0, CALL): (99.0, 101.0), (1000.0, CALL): (100.0, 104.0)}  # mids 100 and 102: inverted
    assert flagged(quotes) == set()  # yet one price (100) fits both quotes


def test_overlapping_spreads_at_the_width_bound_are_not_impossible_either():
    quotes = {(900.0, CALL): (190.0, 210.0), (1000.0, CALL): (95.0, 97.0)}  # mids 200 and 96: a mid rule says 104
    assert flagged(quotes) == set()  # yet 193 against 96 fits inside the width of 100


def test_the_width_bound_is_inclusive_and_a_rupee_over_it_is_impossible():
    assert flagged({(900.0, CALL): (200.0, 200.0), (1000.0, CALL): (100.0, 100.0)}) == set()  # worth exactly 100
    assert flagged({(900.0, CALL): (201.0, 201.0), (1000.0, CALL): (100.0, 100.0)}) == {(900.0, CALL), (1000.0, CALL)}


def test_the_zero_bound_is_inclusive_too():
    assert flagged({(900.0, CALL): (100.0, 100.0), (1000.0, CALL): (100.0, 100.0)}) == set()
    assert flagged({(900.0, CALL): (99.0, 99.0), (1000.0, CALL): (100.0, 100.0)}) == {(900.0, CALL), (1000.0, CALL)}


def test_single_leg_bounds_a_call_bid_above_the_index_and_a_put_bid_above_its_strike():
    assert flagged({(1400.0, CALL): (1051.0, 1052.0)}) == {(1400.0, CALL)}
    assert flagged({(1400.0, CALL): (1050.0, 1052.0)}) == set()
    assert flagged({(700.0, PUT): (701.0, 702.0)}) == {(700.0, PUT)}
    assert flagged({(700.0, PUT): (700.0, 702.0)}) == set()


def test_a_wide_quote_between_two_tight_ones_cannot_hide_a_broken_wider_vertical():
    quotes = {(900.0, CALL): (10.0, 10.0), (1000.0, CALL): (5.0, 25.0), (1100.0, CALL): (20.0, 20.0)}
    assert flagged(quotes) == {(900.0, CALL), (1100.0, CALL)}  # each neighbour pair fits; 900 against 1100 does not


def test_float_noise_at_a_bound_is_not_impossible():
    assert flagged({(900.0, CALL): (200.0 + 1e-12, 200.0), (1000.0, CALL): (100.0, 100.0)}) == set()


def test_among_judges_only_the_legs_given_so_a_far_wing_cannot_flag_the_money():
    snapshot = snapshot_of(
        {(900.0, CALL): (150.0, 151.0), (1000.0, CALL): (100.0, 101.0), (1400.0, CALL): (500.0, 501.0)}
    )
    near = [b.key(900.0, CALL), b.key(1000.0, CALL)]
    assert impossible_keys(snapshot, near) == frozenset() and len(impossible_keys(snapshot)) == 3


def test_neighbours_decide_for_wider_verticals_and_a_gap_in_strikes_does_not_hide_a_break():
    quotes = {(800.0, CALL): (150.0, 151.0), (1000.0, CALL): (100.0, 101.0), (1200.0, CALL): (150.0, 151.0)}
    assert flagged(quotes) == {(1000.0, CALL), (1200.0, CALL)}  # the 1200 call dearer than the 1000 call


def test_legs_that_are_not_two_sided_are_left_out_not_flagged():
    base = snapshot_of({(1000.0, CALL): (100.0, 101.0)})
    quotes = {**base.quotes, b.key(900.0, CALL): SlotQuote(None, 5000.0, None, 10, None, False)}
    assert impossible_keys(replace(base, quotes=quotes)) == frozenset()


def test_different_expiries_and_kinds_are_judged_apart():
    other = b.snapshot(quotes={
        b.key(900.0, CALL): b.quote(100.0, 101.0),
        b.key(1000.0, PUT): b.quote(120.0, 121.0),  # a put at 1000 dearer than a call at 900 means nothing
    })  # fmt: skip
    assert impossible_keys(other) == frozenset()


@pytest.mark.parametrize("worth", [-30.0, -0.01, 0.0, 40.0, 100.0, 100.01, 130.0])
@pytest.mark.parametrize("kind", [CALL, PUT])
def test_it_agrees_with_edge1s_own_vertical_test_when_each_quote_is_a_single_price(kind, worth):
    study = str(Path(__file__).resolve().parents[3] / "research" / "edge1")
    if study not in sys.path:
        sys.path.insert(0, study)
    from edge1study.verticals import valid

    from fno.research_engine.structures import BOUGHT, SOLD, Leg

    dearer, cheaper = 150.0, 150.0 - worth
    if kind is CALL:  # a credit call spread sells the lower strike
        legs, quotes = (
            [Leg(900.0, "CE", SOLD), Leg(1000.0, "CE", BOUGHT)],
            {(900.0, CALL): dearer, (1000.0, CALL): cheaper},
        )
    else:  # a credit put spread sells the higher strike
        legs, quotes = (
            [Leg(1000.0, "PE", SOLD), Leg(900.0, "PE", BOUGHT)],
            {(1000.0, PUT): dearer, (900.0, PUT): cheaper},
        )
    prices = [dearer, cheaper]
    both = flagged({k: (p, p) for k, p in quotes.items()}) == set(quotes)
    assert both == (not valid(legs, prices))
