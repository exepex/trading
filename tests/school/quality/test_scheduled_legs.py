"""Judge 483 finding 1: the leg denominator is what NSE listed for the band, never what the capture holds. A strike the
capture dropped is a leg observed and not passed."""

from dataclasses import replace

import pytest

from fno.school.constants import ClosureReason, OptionKind
from fno.school.contracts.snapshot import ContractKey
from fno.school.quality.capture_gate import GATE_SESSIONS
from fno.school.quality.gate import LegCounts, RoadQualityGate
from fno.school.quality.ports import ListingUnavailable
from tests.school.quality.stack import good
from tests.school.roads.capture_builder import MONTHLIES, FixtureListing

CALL, PUT = OptionKind.CALL, OptionKind.PUT


def opened():
    stack = good()
    road_day = stack.road_day()
    return road_day, stack.snapshots.for_road(road_day)


def without(snapshot, *keys):
    return replace(snapshot, quotes={k: q for k, q in snapshot.quotes.items() if k not in keys})


def test_one_dropped_near_money_strike_lowers_the_share_it_does_not_shrink_the_denominator():
    road_day, snapshot = opened()
    gate = RoadQualityGate(FixtureListing(), band_steps=1)  # 900, 1000, 1100 x two kinds x two expiries: 12 scheduled
    assert gate.legs(road_day, snapshot) == LegCounts(12, 12)
    dropped = without(snapshot, ContractKey(MONTHLIES[0], 1100.0, CALL))
    assert gate.legs(road_day, dropped) == LegCounts(12, 11), "28 of 28 would hide the dropped strike"


def test_a_whole_strike_dropped_on_both_kinds_and_expiries_costs_four_legs():
    road_day, snapshot = opened()
    gone = [ContractKey(e, 1100.0, kind) for e in MONTHLIES for kind in OptionKind]
    assert RoadQualityGate(FixtureListing(), band_steps=1).legs(road_day, without(snapshot, *gone)) == LegCounts(12, 8)


def test_extra_contracts_the_capture_holds_beyond_the_listing_are_not_scheduled():
    road_day, snapshot = opened()
    listed = FixtureListing(keys=frozenset(k for k in snapshot.quotes if k.strike != 1100.0))
    assert RoadQualityGate(listed, band_steps=1).legs(road_day, snapshot) == LegCounts(8, 8)


def test_the_band_is_taken_from_the_listing_so_a_dropped_money_strike_does_not_move_it():
    road_day, snapshot = opened()
    gone = [ContractKey(e, 1000.0, kind) for e in MONTHLIES for kind in OptionKind]  # the strike nearest the spot
    assert RoadQualityGate(FixtureListing(), band_steps=1).legs(road_day, without(snapshot, *gone)) == LegCounts(12, 8)


def test_an_unreadable_listing_raises_listing_unavailable():
    road_day, snapshot = opened()
    with pytest.raises(ListingUnavailable):
        RoadQualityGate(FixtureListing(unavailable=True)).legs(road_day, snapshot)


def test_the_capture_gate_counts_an_unreadable_listing_as_a_failed_session_not_a_crash():
    from datetime import date

    from tests.school.quality.test_capture_gate import report_of

    through = date(2026, 11, 9)
    _, report = report_of(through)
    report.gate = RoadQualityGate(FixtureListing(unavailable=True))
    gate = report.build(through)[0]
    assert {v.closure for v in gate.sessions} == {ClosureReason.EXPIRY_MISMATCH} and len(gate.sessions) == GATE_SESSIONS
    assert not gate.passed
