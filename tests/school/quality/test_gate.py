"""Criteria 2 and 3 of story MS-P1b for the quality gate: the snapshot is the road-day's own and can be priced, with
exactly one reason when it is not; and the leg observations the capture gate counts."""

from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from fno.school.constants import ClosureReason, OptionKind, RoadCode
from fno.school.contracts.roads import OPEN, RoadStatus
from fno.school.quality.band import band_keys
from fno.school.quality.gate import LegCounts, RoadQualityGate
from fno.school.quality.prices import impossible_keys
from tests.school.quality.stack import GATE, good
from tests.school.roads.capture_builder import IST, MONTHLIES, SESSION

CALL = OptionKind.CALL


def opened(**changes):
    """The planted capture's road-day and snapshot, the snapshot optionally changed."""
    stack = good()
    road_day = stack.road_day()
    return road_day, replace(stack.snapshots.for_road(road_day), **changes)


def with_quote(snapshot, strike, **changes):
    key = next(k for k in snapshot.quotes if k.strike == strike and k.kind is CALL and k.expiry == MONTHLIES[0])
    return replace(snapshot, quotes={**snapshot.quotes, key: replace(snapshot.quotes[key], **changes)})


def test_a_good_capture_passes_the_gate():
    road_day, snapshot = opened()
    assert GATE.check(road_day, snapshot) == OPEN


def test_a_road_the_catalogue_closed_keeps_its_one_reason():
    closed = good(tamper=True)
    road_day = closed.road_day()
    _, snapshot = opened()
    assert GATE.check(road_day, snapshot) == RoadStatus(ClosureReason.HASH_MISMATCH)


def test_a_snapshot_that_started_outside_the_window_closes_the_road_out_of_window():
    road_day, snapshot = opened()
    late = snapshot.started_at.replace(hour=15, minute=40)
    result = GATE.check(road_day, replace(snapshot, started_at=late, finished_at=late + timedelta(minutes=1)))
    assert result == RoadStatus(ClosureReason.OUT_OF_WINDOW)


def test_expiries_other_than_the_road_days_close_it_with_expiry_mismatch():
    road_day, snapshot = opened()
    assert (
        GATE.check(road_day, replace(snapshot, expiries=snapshot.expiries[:1])).closed_by
        is ClosureReason.EXPIRY_MISMATCH
    )


def test_an_impossible_price_in_the_band_closes_the_road():
    road_day, snapshot = opened()
    bad = with_quote(snapshot, 1000.0, bid=900.0, ask=901.0)  # a call bid far above the index
    assert GATE.check(road_day, bad) == RoadStatus(ClosureReason.IMPOSSIBLE_PRICE)


def test_an_impossible_price_outside_the_band_does_not():
    road_day, snapshot = opened()
    bad = with_quote(snapshot, 1400.0, bid=2000.0, ask=2001.0)  # four steps from the money; the band is two
    assert RoadQualityGate(band_steps=2).check(road_day, bad) == OPEN
    assert RoadQualityGate(band_steps=4).check(road_day, bad) == RoadStatus(ClosureReason.IMPOSSIBLE_PRICE)


def test_every_fault_at_once_gives_the_first_reason_only():
    road_day, snapshot = opened()
    late = datetime(SESSION.year, SESSION.month, SESSION.day, 16, 0, tzinfo=IST)
    broken = with_quote(replace(snapshot, started_at=late, finished_at=late, expiries=snapshot.expiries[:1]), 1000.0,
                        bid=900.0, ask=901.0)  # fmt: skip
    assert GATE.check(road_day, broken) == RoadStatus(ClosureReason.OUT_OF_WINDOW)


def test_a_snapshot_of_another_road_or_day_is_an_error_not_a_verdict():
    road_day, snapshot = opened()
    with pytest.raises(ValueError):
        GATE.check(road_day, replace(snapshot, road=RoadCode.NIFTY_MONTHLY))
    with pytest.raises(ValueError):
        GATE.check(road_day, replace(snapshot, session=SESSION + timedelta(days=1)))


def test_leg_observations_count_valid_two_sided_legs_in_the_band_of_every_expiry():
    road_day, snapshot = opened()
    gate = RoadQualityGate(band_steps=1)  # strikes 900, 1000, 1100 around the money, both kinds, both expiries
    assert gate.legs(road_day, snapshot) == LegCounts(12, 12)
    one_sided = with_quote(snapshot, 1000.0, ask=None, ask_qty=None)
    invalid = with_quote(one_sided, 900.0, valid=False)
    assert gate.legs(road_day, invalid) == LegCounts(12, 10)
    assert RoadQualityGate(band_steps=10).legs(road_day, snapshot) == LegCounts(32, 32)


def test_an_impossible_leg_does_not_count_as_passed():
    road_day, snapshot = opened()
    bad = with_quote(snapshot, 1000.0, bid=900.0, ask=901.0)
    counts = RoadQualityGate(band_steps=1).legs(road_day, bad)
    assert counts == LegCounts(12, 12 - len(impossible_keys(bad, band_keys(bad, 1))))
    assert counts.passed < 12


def test_the_band_is_a_number_of_strike_steps_around_the_strike_nearest_the_spot():
    road_day, snapshot = opened()
    strikes = lambda steps: sorted({k.strike for k in band_keys(snapshot, steps)})  # noqa: E731
    assert strikes(0) == [1000.0]  # 1050 is level between 1000 and 1100: the lower one
    assert strikes(1) == [900.0, 1000.0, 1100.0]
    assert strikes(10) == [700.0 + 100.0 * n for n in range(8)]
    moved = replace(snapshot, spot=1051.0)
    assert sorted({k.strike for k in band_keys(moved, 0)}) == [1100.0]


def test_a_band_edge_is_in_and_one_strike_more_is_out():
    _, snapshot = opened()
    strikes = {k.strike for k in band_keys(snapshot, 1)}
    assert 1100.0 in strikes and 1200.0 not in strikes  # money 1000; one 100-point step each side
