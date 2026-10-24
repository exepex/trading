"""Part a's one correction resolver and the net check (story MS-INS; judge 501's ruling and judge 503): an original
is read on its close day as its latest correction, never twice; a net that is not its fills' cash is a fault."""

from dataclasses import replace
from datetime import date

import pytest

from fno.school.constants import SLOT_1500, RecordKind
from fno.school.instructor.contracts import DataFault
from fno.school.instructor.reader import record_sha256
from tests.school.drivers.builders import WeekdayCalendar
from tests.school.instructor.builders import (
    SESSIONS,
    decision_record,
    held_trade,
    outcome,
    refilled,
)
from tests.school.instructor.reading import LATER, WriteRefusingDashcam, correct_later, reader


def test_a_correction_sealed_later_replaces_its_original_on_the_original_close_day():
    dashcam = WriteRefusingDashcam()
    fixed = correct_later(dashcam, held_trade(dashcam))
    read = reader(dashcam)
    assert [p.outcome for p in read.closed_on(SESSIONS[2]).paths] == [fixed]
    assert read.closed_on(LATER).paths == ()  # never a path on the day the correction was sealed


@pytest.mark.parametrize("last", [SESSIONS[2], LATER], ids=["correction after the range", "inside it"])
def test_the_days_closed_on_add_up_to_closed_between_over_the_range(last):
    dashcam = WriteRefusingDashcam()
    fixed = correct_later(dashcam, held_trade(dashcam))
    read = reader(dashcam)
    days = WeekdayCalendar().sessions(SESSIONS[0], last)
    by_day = [p.outcome for d in days for p in read.closed_on(d).paths]
    assert by_day == [p.outcome for p in read.closed_between(SESSIONS[0], last).paths] == [fixed]


def test_a_chain_of_corrections_ends_at_the_latest():
    dashcam = WriteRefusingDashcam()
    fixed = correct_later(dashcam, held_trade(dashcam))
    final = correct_later(dashcam, fixed, day=date(2026, 11, 6), exit_price=12.1)
    assert [p.outcome for p in reader(dashcam).closed_on(SESSIONS[2]).paths] == [final]


def test_a_correction_sealed_after_today_is_not_yet_read():
    dashcam = WriteRefusingDashcam()
    record = held_trade(dashcam)
    correct_later(dashcam, record, day=date(2026, 12, 1))  # after CLOCK's day
    assert [p.outcome for p in reader(dashcam).closed_on(SESSIONS[2]).paths] == [record]


def test_a_correction_in_the_same_file_is_read_once():
    dashcam = WriteRefusingDashcam()
    seal = dashcam.seal(SESSIONS[0], SLOT_1500, RecordKind.DECISIONS, (decision_record(SESSIONS[0]),))
    first = outcome(seal.sha256, exit_day=SESSIONS[0])
    fixed = refilled(first, 12.05, corrects=record_sha256(first))
    dashcam.seal(SESSIONS[0], SLOT_1500, RecordKind.OUTCOMES, (first, fixed))
    assert [p.outcome for p in reader(dashcam).closed_on(SESSIONS[0]).paths] == [fixed]


def test_an_outcome_whose_net_is_not_its_fills_cash_is_a_fault():
    """Judge 503: a net moved by Rs -500 would hide in the residual; it is a named fault instead."""
    dashcam = WriteRefusingDashcam()
    record = held_trade(dashcam)
    key = (SESSIONS[2], SLOT_1500, RecordKind.OUTCOMES)
    del dashcam.files[key]
    dashcam.seal(*key, (replace(record, net=record.net - 500.0),))
    (path,) = reader(dashcam).closed_on(SESSIONS[2]).paths
    assert path.faults == (DataFault.NET_MISMATCH_FILLS,)


@pytest.mark.parametrize("off, fault", [(0.01, False), (0.011, True)])
def test_the_net_is_checked_to_a_paisa(off, fault):
    dashcam = WriteRefusingDashcam()
    record = held_trade(dashcam)
    key = (SESSIONS[2], SLOT_1500, RecordKind.OUTCOMES)
    del dashcam.files[key]
    dashcam.seal(*key, (replace(record, net=record.net + off),))
    (path,) = reader(dashcam).closed_on(SESSIONS[2]).paths
    assert (DataFault.NET_MISMATCH_FILLS in path.faults) is fault


def test_an_orphan_is_a_correction_naming_no_outcome_on_file_from_the_start_of_the_record():
    """Judge 522: a correction of an original sealed before any review window is not an orphan; only one whose
    `corrects` names no outcome on file at all, from the start of the record, is."""
    dashcam = WriteRefusingDashcam()
    record = held_trade(dashcam)
    correct_later(dashcam, record)
    assert reader(dashcam).orphan_corrections() == ()  # its original is on file, though sealed before LATER
    stray = refilled(record, 13.0, corrects="ee" * 32, position_id="p9")
    dashcam.locked = False
    dashcam.seal(date(2026, 11, 6), SLOT_1500, RecordKind.OUTCOMES, (stray,))
    assert reader(dashcam).orphan_corrections() == (stray,)
