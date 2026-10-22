"""Criteria 1-3 and 5 of story MS-P1b: five roads on a trading day and none off it, each closure reason of 3.5 from a
planted fixture, exactly one reason a closed road, and the conformance checks of MS-P1a."""

from datetime import date, timedelta

import pytest

from fno.school.constants import ClosureReason, RoadCode
from fno.school.roads.capture import CaptureReader
from fno.school.roads.catalogue import RecordedRoadCatalogue
from fno.school.roads.snapshots import RecordedSnapshotSource
from tests.school.contracts import conformance as c
from tests.school.roads.capture_builder import (
    CALENDAR,
    HOLIDAY,
    LOT,
    MONTHLIES,
    SESSION,
    WEEKEND,
    WEEKLIES,
    DictStore,
    FixedExpiries,
    FixedLots,
    Plant,
    all_roads_planted,
    road,
)

BANK = RoadCode.BANKNIFTY_MONTHLY


def catalogue_over(store, expiries=None, lots=None):
    reader = CaptureReader({dataset: store for dataset in {r.dataset for r in (road(c_) for c_ in RoadCode)}})
    return RecordedRoadCatalogue(CALENDAR, reader, expiries or FixedExpiries(), lots or FixedLots()), reader


def verdicts(catalogue, session=SESSION):
    return {d.road.code: d.status.closed_by for d in catalogue.day(session)}


def test_five_roads_open_on_a_trading_day_with_expiries_lot_and_strike_step():
    store = DictStore()
    all_roads_planted(store)
    days = catalogue_over(store)[0].day(SESSION)
    assert sorted(d.road.code for d in days) == sorted(RoadCode)
    assert all(d.status.open and d.lot == LOT and d.strike_step == 100.0 for d in days)
    expiries = {d.road.code: d.expiries for d in days}
    assert expiries[RoadCode.NIFTY_WEEKLY] == WEEKLIES and expiries[BANK] == MONTHLIES


@pytest.mark.parametrize("closed", [HOLIDAY, WEEKEND, date(2026, 11, 8)], ids=["holiday", "weekend", "muhurat only"])
def test_no_road_on_a_day_that_is_not_a_trading_day(closed):
    store = DictStore()
    all_roads_planted(store, session=closed)  # even a planted capture does not make it a session
    assert catalogue_over(store)[0].day(closed) == ()


FAULTS = {  # the story's order: the first fault in it is the road's one reason
    ClosureReason.CAPTURE_MISSING: {"marker": None},
    ClosureReason.CAPTURE_INCOMPLETE: {"complete": False},
    ClosureReason.OUT_OF_WINDOW: {"started": (15, 30)},
    ClosureReason.HASH_MISMATCH: {"tamper": True},
    ClosureReason.EXPIRY_MISMATCH: {"expiries": (MONTHLIES[0], date(2027, 1, 26))},
}
ORDER = list(FAULTS)


@pytest.mark.parametrize("reason", ORDER)
def test_each_capture_fault_closes_the_road_with_its_reason(reason):
    store = DictStore()
    Plant(road(BANK), **FAULTS[reason]).write(store)
    assert verdicts(catalogue_over(store)[0])[BANK] is reason


@pytest.mark.parametrize(
    "plant",
    [{"marker": "none"}, {"sidecar": False}, {"quote_file": False}],
    ids=["marker says none", "no sidecar", "no quote file"],
)
def test_other_ways_a_capture_can_be_missing(plant):
    store = DictStore()
    Plant(road(BANK), **plant).write(store)
    assert verdicts(catalogue_over(store)[0])[BANK] is ClosureReason.CAPTURE_MISSING


@pytest.mark.parametrize(
    "plant",
    [{"in_window": False}, {"started": (14, 59)}, {"started": (15, 15)}],
    ids=["recorder flag false", "before the window", "after the window"],
)
def test_other_ways_a_capture_can_be_out_of_window(plant):
    store = DictStore()
    Plant(road(BANK), **plant).write(store)
    assert verdicts(catalogue_over(store)[0])[BANK] is ClosureReason.OUT_OF_WINDOW


@pytest.mark.parametrize(
    "code,started,reason",
    [
        (BANK, (15, 1), None),
        (BANK, (15, 13), None),
        (BANK, (15, 14), None),  # the recorder's last instant may stamp itself a moment after the window
        (BANK, (15, 15), ClosureReason.OUT_OF_WINDOW),
        (BANK, (15, 0), ClosureReason.OUT_OF_WINDOW),  # NIFTY's window opens at 14:55, the other indices' at 15:01
        (RoadCode.NIFTY_MONTHLY, (14, 55), None),
        (RoadCode.NIFTY_MONTHLY, (15, 10), None),
        (RoadCode.NIFTY_MONTHLY, (14, 54), ClosureReason.OUT_OF_WINDOW),
        (RoadCode.NIFTY_WEEKLY, (15, 6), None),
        (RoadCode.NIFTY_WEEKLY, (14, 55), ClosureReason.OUT_OF_WINDOW),
    ],
)
def test_window_edges_are_per_road(code, started, reason):
    store = DictStore()
    Plant(road(code), started=started).write(store)
    assert verdicts(catalogue_over(store)[0])[code] is reason


def test_rows_short_of_the_sidecars_count_make_the_capture_incomplete():
    store = DictStore()
    Plant(road(BANK), short_by=1).write(store)
    assert verdicts(catalogue_over(store)[0])[BANK] is ClosureReason.CAPTURE_INCOMPLETE


def test_a_lot_the_source_cannot_find_closes_the_road():
    store = DictStore()
    all_roads_planted(store)
    catalogue, _ = catalogue_over(store, lots=FixedLots(None))
    assert set(verdicts(catalogue).values()) == {ClosureReason.LOT_MISMATCH}


def test_unreadable_expiry_listing_closes_with_expiry_mismatch_rather_than_opening():
    store = DictStore()
    all_roads_planted(store)
    catalogue, _ = catalogue_over(store, expiries=FixedExpiries(unavailable=True))
    assert set(verdicts(catalogue).values()) == {ClosureReason.EXPIRY_MISMATCH}


def test_a_capture_that_differs_from_the_listing_by_one_expiry_is_a_mismatch():
    store = DictStore()
    all_roads_planted(store)
    wrong = {BANK: (MONTHLIES[0],)}
    assert verdicts(catalogue_over(store, expiries=FixedExpiries(wrong))[0])[BANK] is ClosureReason.EXPIRY_MISMATCH


@pytest.mark.parametrize("earlier,later", [(a, b) for i, a in enumerate(ORDER) for b in ORDER[i + 1 :]])
def test_two_faults_give_the_earlier_reason_only(earlier, later):
    store = DictStore()
    Plant(road(BANK), **FAULTS[earlier], **{k: v for k, v in FAULTS[later].items() if k not in FAULTS[earlier]}).write(
        store
    )
    assert verdicts(catalogue_over(store)[0])[BANK] is earlier


def test_a_fault_with_a_lot_fault_behind_it_gives_the_capture_reason_and_never_asks_for_the_lot():
    store = DictStore()
    Plant(road(BANK), tamper=True).write(store)
    lots = FixedLots(None)
    assert verdicts(catalogue_over(store, lots=lots)[0])[BANK] is ClosureReason.HASH_MISMATCH
    assert lots.asked == []


def test_one_faulty_road_never_closes_another():
    store = DictStore()
    planted = all_roads_planted(store)
    Plant(road(RoadCode.FINNIFTY_MONTHLY), tamper=True).write(store)
    got = verdicts(catalogue_over(store)[0])
    assert got.pop(RoadCode.FINNIFTY_MONTHLY) is ClosureReason.HASH_MISMATCH
    assert set(got.values()) == {None} and len(got) == len(planted) - 1


def test_a_closed_road_carries_no_expiries_lot_or_step_to_use():
    store = DictStore()
    Plant(road(BANK), marker=None).write(store)
    closed = next(d for d in catalogue_over(store)[0].day(SESSION) if d.road.code is BANK)
    assert (closed.expiries, closed.lot, closed.strike_step) == ((), None, None) and not closed.status.open


def test_conformance_of_the_catalogue_and_the_snapshot_source():
    store = DictStore()
    all_roads_planted(store)
    Plant(road(BANK), session=SESSION + timedelta(days=1), marker=None).write(store)
    catalogue, reader = catalogue_over(store)
    c.check_road_catalogue(catalogue, SESSION, HOLIDAY)
    closed_store = DictStore()
    Plant(road(BANK), tamper=True).write(closed_store)
    closed_catalogue, closed_reader = catalogue_over(closed_store)
    closed = next(d for d in closed_catalogue.day(SESSION) if d.road.code is BANK)
    opened = next(d for d in catalogue.day(SESSION) if d.road.code is BANK)
    assert closed.status.closed_by is ClosureReason.HASH_MISMATCH
    c.check_snapshot_source(RecordedSnapshotSource(reader), opened, closed)


def test_a_road_day_carries_each_recorded_expiry_s_own_step():
    store = DictStore()
    strikes = {MONTHLIES[0]: tuple(float(s) for s in range(800, 1301, 50)),
               MONTHLIES[1]: tuple(float(s) for s in range(700, 1401, 100))}  # fmt: skip
    Plant(road(BANK), strikes=strikes).write(store)
    day = next(d for d in catalogue_over(store)[0].day(SESSION) if d.road.code is BANK)
    assert day.strike_step == 50.0 and dict(day.strike_steps) == {MONTHLIES[0]: 50.0, MONTHLIES[1]: 100.0}
    assert day.step_for(MONTHLIES[1]) == 100.0


def test_every_open_road_day_names_a_step_for_each_expiry_it_records():
    store = DictStore()
    all_roads_planted(store)
    for day in catalogue_over(store)[0].day(SESSION):
        assert set(day.strike_steps) == set(day.expiries) and day.strike_steps[day.expiries[0]] == day.strike_step
