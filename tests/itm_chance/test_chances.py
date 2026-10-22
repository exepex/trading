"""Criteria 1-2: each contract's chance is G13's own CDF arithmetic, labelled, with its region; no distribution gives
no chance and G13's reason."""

from datetime import date

import pytest

from fno.itm_chance.chances import distribution_of, expiry_chances, itm_chance, region
from fno.itm_chance.constants import BODY, MEASURE, TAIL
from fno.price_distribution.density import Distribution, Tail

from .builders import LOWER, POINTS, UPPER, expiry, record

DAY, EXPIRY = date(2026, 10, 1), date(2026, 10, 27)


def g13_distribution() -> Distribution:
    lower, upper = Tail(LOWER["strike"], LOWER["cdf"], 0.18), Tail(UPPER["strike"], UPPER["cdf"], 0.14)
    return Distribution(23000.0, 26, tuple((k, c) for k, c in POINTS), 0, lower, upper)


def test_the_rebuilt_distribution_is_g13s_own():
    assert distribution_of(expiry(EXPIRY, 26)) == g13_distribution()


@pytest.mark.parametrize("strike", [21000.0, 22000.0, 22250.0, 23000.0, 23800.0, 24000.0, 25500.0])
def test_put_is_f_and_call_is_one_minus_f_and_they_sum_to_one(strike):
    d = g13_distribution()
    put, call = itm_chance(d, strike, "PE"), itm_chance(d, strike, "CE")
    assert put == d.cdf(strike) and call == pytest.approx(1 - d.cdf(strike)) and put + call == pytest.approx(1)


def test_hand_values_inside_the_body_and_on_a_point():
    d = g13_distribution()
    assert itm_chance(d, 22250.0, "PE") == pytest.approx(0.20)  # halfway between 0.10 and 0.30
    assert itm_chance(d, 23000.0, "CE") == pytest.approx(0.45)


def test_tails_follow_g13s_tail_rule_below_and_above():
    d = g13_distribution()
    assert 0 < itm_chance(d, 21000.0, "PE") < 0.10 and 0 < itm_chance(d, 25500.0, "CE") < 0.08


def test_region_is_tail_exactly_outside_the_measured_cdf():
    d = g13_distribution()
    assert [region(d, k) for k in (21999.0, 22000.0, 24000.0, 24001.0)] == [TAIL, BODY, BODY, TAIL]


def test_every_contract_gets_a_labelled_chance_with_its_source():
    found = expiry_chances(record(DAY, [expiry(EXPIRY, 26)]))[0].chances()
    assert {(c.strike, c.side) for c in found} == {(22500.0, "CE"), (22500.0, "PE"), (23000.0, "CE"), (23000.0, "PE")}
    labels = {(c.measure, c.source, c.day, c.expiry, c.days) for c in found}
    assert labels == {(MEASURE, "backfill_eod", DAY, EXPIRY, 26)}


def test_a_3pm_record_is_labelled_3pm():
    assert expiry_chances(record(DAY, [expiry(EXPIRY, 26)], label="live"))[0].source == "3pm"


def test_no_distribution_gives_no_chance_and_g13s_reason():
    found = expiry_chances(record(DAY, [expiry(EXPIRY, 26, ok=False)]))[0]
    assert found.chances() == [] and found.reason == "too few CDF points: 3 (at least 8)"
