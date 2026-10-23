"""Judge 482 finding 1 and plant 7: each expiry has its own strike step, the most common gap of its listed strikes."""

from dataclasses import replace
from datetime import date

from fno.school.constants import OptionKind, RoadCode
from fno.school.contracts.snapshot import ContractKey
from fno.school.quality.band import band_keys
from fno.school.quality.gate import LegCounts, RoadQualityGate
from fno.school.quality.strikes import strike_steps
from fno.school.roads.catalogue import RecordedRoadCatalogue
from tests.school.contracts import builders as b
from tests.school.roads.capture_builder import (
    CALENDAR,
    MONTHLIES,
    SESSION,
    DictStore,
    FixedExpiries,
    FixedLots,
    FixtureListing,
    Plant,
    reader_over_all,
    road,
)

NEAR, FAR = date(2026, 10, 27), date(2026, 11, 23)
CALL = OptionKind.CALL


def keys(expiry, strikes):
    return [ContractKey(expiry, float(s), kind) for s in strikes for kind in OptionKind]


def test_each_expiry_has_its_own_step_as_finnifty_has_on_22_oct():
    chain = keys(NEAR, range(800, 1301, 50)) + keys(FAR, range(700, 1401, 100))
    assert strike_steps(chain) == {NEAR: 50.0, FAR: 100.0}


def test_the_step_is_the_most_common_gap_not_the_least_common_or_the_first():
    strikes = [900, 950, 1000, 1100, 1200, 1300, 1400]  # one gap of 50, then 100 four times, 50 once more
    assert strike_steps(keys(NEAR, strikes)) == {NEAR: 100.0}
    assert strike_steps(keys(NEAR, [100, 200, 300, 350])) == {NEAR: 100.0}


def test_a_tie_goes_to_the_smaller_gap():
    assert strike_steps(keys(NEAR, [100, 150, 250])) == {NEAR: 50.0}


def test_an_expiry_with_fewer_than_two_strikes_has_no_step():
    assert strike_steps(keys(NEAR, [1000]) + keys(FAR, [900, 1000])) == {FAR: 100.0}
    assert strike_steps([]) == {}


def two_step_snapshot():
    quotes = {k: b.quote() for k in keys(NEAR, range(800, 1301, 50)) + keys(FAR, range(700, 1401, 100))}
    return b.snapshot(quotes=quotes)  # spot 1050


def test_the_band_is_built_per_expiry_in_that_expiry_s_own_steps():
    near = {k.strike for k in band_keys(list(two_step_snapshot().quotes), 1050.0, 2) if k.expiry == NEAR}
    far = {k.strike for k in band_keys(list(two_step_snapshot().quotes), 1050.0, 2) if k.expiry == FAR}
    assert near == {950.0, 1000.0, 1050.0, 1100.0, 1150.0}  # money 1050, two 50-point steps each side
    assert far == {800.0, 900.0, 1000.0, 1100.0, 1200.0}  # money 1000 (1050 is level; the lower), two 100-point steps


def test_the_wider_expiry_keeps_a_full_band_not_the_narrow_expiry_s_reach():
    counts = {
        e: sum(1 for k in band_keys(list(two_step_snapshot().quotes), 1050.0, 10) if k.expiry == e) for e in (NEAR, FAR)
    }
    assert counts == {NEAR: 22, FAR: 16}  # 11 and 8 strikes: all that the 800-1300 and 700-1400 chains hold, 2 kinds


def test_a_road_day_built_on_a_two_step_capture_takes_the_nearest_expiry_s_step_and_a_per_expiry_band():
    store = DictStore()
    strikes = {MONTHLIES[0]: tuple(float(s) for s in range(800, 1301, 50)),
               MONTHLIES[1]: tuple(float(s) for s in range(700, 1401, 100))}  # fmt: skip
    Plant(road(RoadCode.BANKNIFTY_MONTHLY), strikes=strikes).write(store)
    reader = reader_over_all(store)
    catalogue = RecordedRoadCatalogue(CALENDAR, reader, FixedExpiries(), FixedLots())
    day = next(d for d in catalogue.day(SESSION) if d.road.code is RoadCode.BANKNIFTY_MONTHLY)
    assert day.status.open and day.strike_step == 50.0
    snapshot = reader.read(day.road, SESSION).snapshot()
    assert RoadQualityGate(FixtureListing(strikes), band_steps=2).legs(day, snapshot) == LegCounts(
        20, 20
    )  # 5 strikes x 2 kinds x 2 expiries


def test_the_recorded_finnifty_shape_49_strikes_at_50_and_25_at_100_gives_a_full_band_on_each_expiry():
    """The shape the recorder wrote on 21 and 22 Oct 2026 (judge 482), on a synthetic grid: one step for both expiries
    gave the later one 11 strikes a side kind instead of 21."""
    near = keys(NEAR, [1000 + 50 * n for n in range(49)])
    far = keys(FAR, [1000 + 100 * n for n in range(25)])
    snapshot = b.snapshot(quotes={k: b.quote() for k in near + far})
    middle = 1000 + 50 * 24
    snapshot = replace(snapshot, spot=float(middle))
    band = band_keys(list(snapshot.quotes), snapshot.spot, 10)
    assert strike_steps(snapshot.quotes) == {NEAR: 50.0, FAR: 100.0}
    assert {e: sum(1 for k in band if k.expiry == e) for e in (NEAR, FAR)} == {NEAR: 42, FAR: 42}
