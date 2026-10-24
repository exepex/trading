"""Story MS-P1a4: each recorded expiry's own dated lot. NSE changes a lot from a given expiry, so for a while an
index's two monthlies carry different lots; a proposal on one expiry is sized with that expiry's lot, never
another's."""

import dataclasses
from datetime import date

import pytest

from fno.school.constants import RoadCode
from fno.school.contracts.roads import DatedLot
from tests.school.contracts import builders as b

LATER = date(2026, 12, 29)
OLD, NEW = DatedLot(15, "lot file, Nov expiry"), DatedLot(30, "lot file, from the Dec expiry")


def two_expiries(lots, lot=OLD):
    day = b.road_day(RoadCode.BANKNIFTY_MONTHLY)
    return dataclasses.replace(day, expiries=(b.EXPIRY, LATER), lot=lot, strike_steps={}, lots=lots)


def test_each_expiry_has_its_own_lot():
    day = two_expiries({b.EXPIRY: OLD, LATER: NEW})
    assert (day.lot_for(b.EXPIRY), day.lot_for(LATER)) == (OLD, NEW) and day.lot == OLD


def test_without_lots_every_recorded_expiry_carries_the_road_s_lot_and_no_other_expiry_has_one():
    day = two_expiries({})
    assert day.lot_for(b.EXPIRY) == day.lot_for(LATER) == OLD
    with pytest.raises(ValueError):
        day.lot_for(date(2027, 1, 26))  # an expiry the road did not record


def test_with_lots_an_unrecorded_expiry_is_never_given_another_s_lot():
    with pytest.raises(ValueError):
        two_expiries({b.EXPIRY: OLD, LATER: NEW}).lot_for(date(2027, 1, 26))


WRONG = ({b.EXPIRY: OLD}, {b.EXPIRY: OLD, LATER: DatedLot(0, "x")}, {b.EXPIRY: NEW, LATER: NEW},
         {b.EXPIRY: OLD, LATER: NEW, date(2027, 1, 26): NEW})  # fmt: skip


@pytest.mark.parametrize("lots", WRONG)
def test_wrong_lots_are_refused(lots):
    with pytest.raises(ValueError):
        two_expiries(lots)


def test_a_road_day_stays_hashable_with_its_lots():
    assert hash(two_expiries({b.EXPIRY: OLD, LATER: NEW})) == hash(two_expiries({}))
