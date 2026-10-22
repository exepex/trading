"""Criterion 3 (story MS-P1h): five roads on one day are one cluster; the common group needs every control counted."""

from datetime import timedelta

from fno.school.constants import RoadCode
from fno.school.registration.clusters import common_road_days, session_clusters
from tests.school.registration.fakes import SESSION, candidate

ALL_ROADS = tuple(RoadCode)


def day_of(driver: str, session=SESSION, roads=ALL_ROADS):
    return [candidate(driver_id=driver, session=session, road=road) for road in roads]


def test_five_roads_on_one_day_form_one_cluster_and_count_as_one_session():
    group = common_road_days(day_of("CS1@1"), ["CS1@1"])
    assert len(group) == 5
    clusters = session_clusters(group)
    assert list(clusters) == [SESSION] and clusters[SESSION] == frozenset(ALL_ROADS)


def test_two_sessions_are_two_clusters():
    group = common_road_days(day_of("CS1@1") + day_of("CS1@1", SESSION + timedelta(days=1)), ["CS1@1"])
    assert list(session_clusters(group)) == [SESSION, SESSION + timedelta(days=1)]


def test_the_common_group_holds_only_road_days_every_control_has_counted():
    counted = day_of("CS1@1") + day_of("N0@1") + day_of("RC1@1", roads=ALL_ROADS[:3])
    group = common_road_days(counted, ["CS1@1", "N0@1", "RC1@1"])
    assert {road for _, road in group} == set(ALL_ROADS[:3])


def test_a_driver_with_nothing_counted_leaves_an_empty_group():
    assert common_road_days(day_of("CS1@1"), ["CS1@1", "N0@1"]) == frozenset()


def test_no_drivers_and_no_road_days_give_nothing():
    assert common_road_days(day_of("CS1@1"), []) == frozenset()
    assert session_clusters([]) == {}
