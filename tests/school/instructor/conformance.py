"""Conformance checks for the instructor's ports (story MS-INS, part a): each real adapter's tests call the check for
its port with its own object, as the fakes' tests do. A check uses only the contract."""

from datetime import date

import pytest

from fno.school.instructor.ports import (
    CardReplay,
    EventCalendar,
    InstructorConflict,
    InstructorKind,
    InstructorStore,
    SnapshotArchive,
)


def check_snapshot_archive(archive, road, recorded: date, missing: date) -> None:
    assert isinstance(archive, SnapshotArchive)
    found = archive.snapshot(road, recorded)
    assert found is not None and found.road == road and found.session == recorded
    assert archive.snapshot(road, missing) is None


def check_event_calendar(calendar, event_day: date, known_on: date) -> None:
    assert isinstance(calendar, EventCalendar)
    assert calendar.known_between(known_on, event_day.replace(day=1), event_day) == (event_day,)
    assert calendar.known_between(known_on, event_day, event_day) == ()  # "after" is strict
    before = date.fromordinal(known_on.toordinal() - 1)
    assert calendar.known_between(before, event_day.replace(day=1), event_day) == ()  # not yet known


def check_card_replay(replay, record) -> None:
    assert isinstance(replay, CardReplay)
    result = replay.replay(record)
    assert result is None or (result.driver_id, result.road, result.session) == (
        record.decision.driver_id,
        record.road,
        record.session,
    )


def check_instructor_store(store, session: date, records: tuple, other: tuple) -> None:
    assert isinstance(store, InstructorStore)
    assert store.read(session, InstructorKind.CAUSES) is None
    first = store.write(session, InstructorKind.CAUSES, records)
    assert store.write(session, InstructorKind.CAUSES, records) == first  # the same bytes: a no-op
    with pytest.raises(InstructorConflict):
        store.write(session, InstructorKind.CAUSES, other)
    assert store.read(session, InstructorKind.CAUSES) == records
