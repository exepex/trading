"""Part a's reader on damaged or unusual days (story MS-INS; judge 501): a damaged sealed file is a fault or an
unreadable day, never a crash; an outcome sealed mid-range is read; a muhurat-only session is not required."""

from dataclasses import replace

from fno.school.constants import SLOT_1500, RecordKind
from fno.school.fakes import FakeSettlementSource
from fno.school.instructor.contracts import DataFault
from fno.school.instructor.reader import PathReader
from tests.school.drivers.builders import WeekdayCalendar
from tests.school.instructor.builders import (
    SESSIONS,
    held_trade,
    outcome,
)
from tests.school.instructor.reading import CLOCK, WriteRefusingDashcam, reader


def test_a_damaged_held_day_is_a_fault_on_its_path_and_the_rest_still_reads():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam)
    dashcam.damaged = frozenset({(SESSIONS[1], RecordKind.DECISIONS)})
    (path,) = reader(dashcam).closed_on(SESSIONS[2]).paths
    assert path.faults == (DataFault.SEALED_FILE_DAMAGED,)


def test_a_damaged_entry_day_is_a_fault_not_a_crash():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam)
    dashcam.damaged = frozenset({(SESSIONS[0], RecordKind.DECISIONS)})
    (path,) = reader(dashcam).closed_on(SESSIONS[2]).paths
    assert path.entry is None and DataFault.SEALED_FILE_DAMAGED in path.faults
    assert DataFault.ENTRY_DECISION_MISSING not in path.faults  # damaged, not missing: the fault says which


def test_a_damaged_outcomes_file_is_reported_and_the_other_days_still_come_back():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam)
    early = dashcam.seal(SESSIONS[0], SLOT_1500, RecordKind.OUTCOMES, (outcome(
        dashcam.find(SESSIONS[0], SLOT_1500, RecordKind.DECISIONS).sha256, exit_day=SESSIONS[0]),))  # fmt: skip
    assert early
    dashcam.damaged = frozenset({(SESSIONS[0], RecordKind.OUTCOMES)})
    read = reader(dashcam).closed_between(SESSIONS[0], SESSIONS[2])
    assert read.unreadable == (SESSIONS[0],) and [p.outcome.exit.filled_at.date() for p in read.paths] == [SESSIONS[2]]


def test_an_outcome_sealed_mid_range_is_read():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam)
    seal = dashcam.find(SESSIONS[0], SLOT_1500, RecordKind.DECISIONS)
    middle = replace(outcome(seal.sha256, exit_day=SESSIONS[0]), position_id="p0")
    dashcam.seal(SESSIONS[1], SLOT_1500, RecordKind.OUTCOMES, (middle,))
    ids = [p.outcome.position_id for p in reader(dashcam).closed_between(SESSIONS[0], SESSIONS[2]).paths]
    assert ids == ["p0", "p1"]


class MuhuratCalendar(WeekdayCalendar):
    """The middle fixture session is a muhurat-only evening: a session, but not a trading day."""

    def session_kind(self, day):
        return "muhurat" if day == SESSIONS[1] else super().session_kind(day)


def test_a_muhurat_only_session_inside_a_hold_is_not_required():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam)
    del dashcam.files[(SESSIONS[1], SLOT_1500, RecordKind.DECISIONS)]
    plain = reader(dashcam)
    muhurat = PathReader(dashcam, plain.snapshots, FakeSettlementSource(), MuhuratCalendar(), CLOCK)
    (path,) = muhurat.closed_on(SESSIONS[2]).paths
    assert path.attributable and [s.session for s in path.snapshots] == [SESSIONS[0], SESSIONS[2]]
