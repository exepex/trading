"""Story MS-P1a2: each recorded expiry's own strike step, and a closed road's detail."""

import dataclasses
from datetime import date

import pytest

from fno.school.constants import ROAD_DETAIL_INPUT, ClosureReason, RoadCode
from fno.school.contracts.records import DecisionRecord
from fno.school.contracts.roads import ROADS, RoadStatus
from fno.school.fakes import FakeRoadCatalogue
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c
from tests.school.contracts.test_records import closed_record

LATER = date(2026, 12, 29)


def two_expiries(steps):
    day = b.road_day(RoadCode.FINNIFTY_MONTHLY)
    return dataclasses.replace(day, expiries=(b.EXPIRY, LATER), strike_step=50.0, strike_steps=steps)


def test_a_later_expiry_has_its_own_step():
    day = two_expiries({b.EXPIRY: 50.0, LATER: 100.0})
    assert (day.step_for(b.EXPIRY), day.step_for(LATER)) == (50.0, 100.0)


def test_without_steps_only_the_nearest_expiry_s_step_is_known():
    day = two_expiries({})
    assert day.step_for(b.EXPIRY) == 50.0
    with pytest.raises(ValueError):
        day.step_for(LATER)  # never borrowed from the nearest expiry


@pytest.mark.parametrize("steps", [{b.EXPIRY: 50.0}, {b.EXPIRY: 50.0, LATER: 0.0}, {b.EXPIRY: 100.0, LATER: 100.0},
                                   {b.EXPIRY: 50.0, LATER: 100.0, date(2027, 1, 26): 100.0}])  # fmt: skip
def test_wrong_steps_are_refused(steps):
    with pytest.raises(ValueError):
        two_expiries(steps)


def test_a_road_day_stays_hashable_with_its_steps():
    assert hash(two_expiries({b.EXPIRY: 50.0, LATER: 100.0}))


def test_a_closed_road_carries_its_detail_and_an_open_one_none():
    closed = RoadStatus(ClosureReason.EXPIRY_MISMATCH, "listing unreadable: no Nov contracts in the master file")
    assert not closed.open and closed.detail
    with pytest.raises(ValueError):
        RoadStatus(None, "a detail without a closure")


def test_the_detail_is_recorded_in_the_decision_inputs():
    record = dataclasses.replace(closed_record(), inputs={ROAD_DETAIL_INPUT: "listing unreadable"})
    assert DecisionRecord.from_bytes(record.to_bytes()).inputs[ROAD_DETAIL_INPUT] == "listing unreadable"


def test_the_catalogue_check_refuses_an_open_road_without_every_expiry_s_step():
    days = tuple(dataclasses.replace(b.road_day(r.code), strike_steps={}) for r in ROADS)
    with pytest.raises(AssertionError):
        c.check_road_catalogue(FakeRoadCatalogue({b.SESSION: days}), b.SESSION, LATER)
