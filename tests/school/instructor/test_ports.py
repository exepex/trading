"""Part a's ports (story MS-INS, criterion 7): the fakes and the real read adapters pass the conformance checks."""

from dataclasses import replace
from datetime import date

from fno.research_data.events import Event
from fno.school.constants import ClosureReason
from fno.school.contracts.roads import RoadStatus
from fno.school.fakes import FakeRoadCatalogue, FakeSnapshotSource
from fno.school.instructor.adapters import RecordedEventCalendar, RecordedSnapshotArchive
from fno.school.instructor.fakes import (
    FakeCardReplay,
    FakeEventCalendar,
    FakeInstructorStore,
    FakeSnapshotArchive,
)
from tests.school.contracts.builders import road_day
from tests.school.instructor.builders import ROAD, SESSIONS, attribution, decision_record, snap
from tests.school.instructor.conformance import (
    check_card_replay,
    check_event_calendar,
    check_instructor_store,
    check_snapshot_archive,
)

EVENT_DAY, KNOWN_ON = date(2026, 12, 5), date(2026, 11, 3)


def test_the_fakes_conform():
    check_snapshot_archive(
        FakeSnapshotArchive({(ROAD, SESSIONS[0]): snap(SESSIONS[0])}), ROAD, SESSIONS[0], SESSIONS[1]
    )
    check_event_calendar(FakeEventCalendar({EVENT_DAY: KNOWN_ON}), EVENT_DAY, KNOWN_ON)
    check_card_replay(FakeCardReplay(), decision_record(SESSIONS[0]))
    check_instructor_store(
        FakeInstructorStore(), SESSIONS[0], (attribution(),), (attribution(theta=76.0, residual=-1.0),)
    )


def _archive(open_days, closed_days=()) -> RecordedSnapshotArchive:
    days = {d: (replace(road_day(ROAD), session=d),) for d in open_days}
    days |= {d: (replace(road_day(ROAD, RoadStatus(ClosureReason.CAPTURE_MISSING)), session=d),) for d in closed_days}
    return RecordedSnapshotArchive(FakeRoadCatalogue(days), FakeSnapshotSource({(ROAD, d): snap(d) for d in open_days}))


def test_the_recorded_snapshot_archive_conforms():
    check_snapshot_archive(_archive([SESSIONS[0]]), ROAD, SESSIONS[0], SESSIONS[1])


def test_the_archive_gives_none_for_a_closed_road_and_for_a_capture_the_source_cannot_give():
    assert _archive([], [SESSIONS[0]]).snapshot(ROAD, SESSIONS[0]) is None
    catalogue = FakeRoadCatalogue({SESSIONS[0]: (replace(road_day(ROAD), session=SESSIONS[0]),)})
    assert RecordedSnapshotArchive(catalogue, FakeSnapshotSource()).snapshot(ROAD, SESSIONS[0]) is None


def test_the_recorded_event_calendar_conforms_on_a6s_known_on_rule():
    event = Event(EVENT_DAY, "rbi_policy", True, KNOWN_ON, "fixture")
    check_event_calendar(RecordedEventCalendar([event]), EVENT_DAY, KNOWN_ON)


def test_an_unscheduled_event_is_never_known_ahead():
    event = Event(EVENT_DAY, "rbi_policy", False, None, "fixture")
    assert RecordedEventCalendar([event]).known_between(EVENT_DAY, KNOWN_ON, EVENT_DAY) == ()


def test_the_composition_root_builds_the_event_calendar_from_a6s_file():
    from fno.school.instructor.ports import EventCalendar
    from fno.school.instructor.wiring import build_event_calendar

    assert isinstance(build_event_calendar(), EventCalendar)
