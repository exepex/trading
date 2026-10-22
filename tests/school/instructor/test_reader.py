"""Part a's path reader (story MS-INS, criteria 1-5): closed trades and tickets joined to their sealed decision, exit
record and verified snapshots; every unverifiable input a data fault, never a guess. Criterion 5 (reads only): the
dashcam below refuses any write once the fixtures are laid, and every other port the reader holds has no write method;
the whole instructor run is checked on the fake fleet again when part e joins the parts."""

from dataclasses import replace
from datetime import date, datetime

import pytest

from fno.school.constants import SLOT_1500, ExitReason, Outcome, RecordKind, RoadCode
from fno.school.contracts.accounts import SettlementPrice
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.records import DecisionRecord, ExitRecord
from fno.school.contracts.seal import StaleSeal
from fno.school.fakes import FakeDashcam, FakeSettlementSource
from fno.school.instructor.contracts import DataFault
from fno.school.instructor.fakes import FakeSnapshotArchive
from fno.school.instructor.reader import PathReader, record_sha256
from tests.school.contracts.builders import IST
from tests.school.drivers.builders import WeekdayCalendar
from tests.school.instructor.builders import (
    DRIVER,
    OTHER,
    ROAD,
    SESSIONS,
    closed_record,
    decision_record,
    held_trade,
    outcome,
    snap,
)

LATER = date(2026, 11, 5)
CLOCK = FixedClock(datetime(2026, 11, 30, 21, 0, tzinfo=IST))  # "today": after every fixture's file
OTHER_ROAD = RoadCode.NIFTY_MONTHLY


class WriteRefusingDashcam(FakeDashcam):
    """The read-only proof: any seal after the fixtures are laid fails the test. A file named in `damaged` reads as
    the real store reads bytes that differ from their seal: `StaleSeal`."""

    locked = False
    damaged: frozenset = frozenset()

    def seal(self, *args, **kwargs):
        assert not self.locked, "the instructor wrote into the dashcam"
        return super().seal(*args, **kwargs)

    def read(self, seal):
        if any(seal.path.endswith(f"{d:%Y/%m/%d}/1500.{kind}.jsonl.gz") for d, kind in self.damaged):
            raise StaleSeal(seal.path)
        return super().read(seal)


def reader(dashcam, archive=None, settlements=None) -> PathReader:
    archive = archive or FakeSnapshotArchive({(ROAD, d): snap(d) for d in SESSIONS})
    dashcam.locked = True
    return PathReader(dashcam, archive, settlements or FakeSettlementSource(), WeekdayCalendar(), CLOCK)


def test_a_trade_held_three_sessions_has_its_three_snapshots_in_order():
    dashcam = WriteRefusingDashcam()
    record = held_trade(dashcam)
    (path,) = reader(dashcam).closed_on(SESSIONS[2]).paths
    assert path.outcome == record and path.attributable and not path.is_ticket
    assert [s.session for s in path.snapshots] == list(SESSIONS)
    assert path.entry.decision.driver_id == record.driver_id and path.exit.position_id == "p1"


def test_a_ticket_is_read_as_a_ticket_against_its_ticket_decision():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam, ticket=True)
    (path,) = reader(dashcam).closed_on(SESSIONS[2]).paths
    assert path.is_ticket and path.attributable and path.entry.decision.outcome == "ticket"


def test_a_closed_road_mid_hold_skips_that_session_without_a_fault():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam, closed_middle=True)
    (path,) = reader(dashcam).closed_on(SESSIONS[2]).paths
    assert path.attributable and path.sessions_skipped == 1
    assert [s.session for s in path.snapshots] == [SESSIONS[0], SESSIONS[2]]


def correct_later(dashcam, record, day=LATER, net=-96.0):
    fixed = replace(record, net=net, corrects=record_sha256(record))
    dashcam.locked = False
    dashcam.seal(day, SLOT_1500, RecordKind.OUTCOMES, (fixed,))  # its own session: the first file is never rewritten
    return fixed


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
    final = correct_later(dashcam, fixed, day=date(2026, 11, 6), net=-97.0)
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
    fixed = replace(first, net=-96.0, corrects=record_sha256(first))
    dashcam.seal(SESSIONS[0], SLOT_1500, RecordKind.OUTCOMES, (first, fixed))
    assert [p.outcome for p in reader(dashcam).closed_on(SESSIONS[0]).paths] == [fixed]


def test_a_snapshot_whose_hash_differs_from_its_decision_record_is_a_data_fault():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam)
    archive = FakeSnapshotArchive({(ROAD, d): snap(d) for d in SESSIONS})
    archive.snapshots[(ROAD, SESSIONS[1])] = snap(SESSIONS[1], sha="99" * 32)
    (path,) = reader(dashcam, archive).closed_on(SESSIONS[2]).paths
    assert path.faults == (DataFault.SNAPSHOT_HASH_MISMATCH,) and not path.attributable


def test_a_missing_entry_snapshot_is_a_data_fault():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam)
    archive = FakeSnapshotArchive({(ROAD, d): snap(d) for d in SESSIONS[1:]})
    (path,) = reader(dashcam, archive).closed_on(SESSIONS[2]).paths
    assert DataFault.SNAPSHOT_MISSING in path.faults


def test_an_outcome_naming_another_decision_file_is_a_seal_mismatch():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam)
    key = (SESSIONS[2], SLOT_1500, RecordKind.OUTCOMES)
    del dashcam.files[key]
    dashcam.seal(*key, (outcome("77" * 32),))
    (path,) = reader(dashcam).closed_on(SESSIONS[2]).paths
    assert path.faults == (DataFault.ENTRY_SEAL_MISMATCH,)


def test_an_outcome_without_its_entry_decision_is_a_fault():
    dashcam = WriteRefusingDashcam()
    seal = dashcam.seal(SESSIONS[0], SLOT_1500, RecordKind.DECISIONS, (decision_record(SESSIONS[0], "REF@1"),))
    dashcam.seal(SESSIONS[0], SLOT_1500, RecordKind.OUTCOMES, (outcome(seal.sha256, exit_day=SESSIONS[0]),))
    (path,) = reader(dashcam).closed_on(SESSIONS[0]).paths
    assert path.entry is None and DataFault.ENTRY_DECISION_MISSING in path.faults


def settled_by_expiry(dashcam) -> date:
    seal = dashcam.seal(SESSIONS[0], SLOT_1500, RecordKind.DECISIONS, (decision_record(SESSIONS[0]),))
    expiry = SESSIONS[1]
    dashcam.seal(expiry, SLOT_1500, RecordKind.DECISIONS, (decision_record(expiry, OTHER),))
    dashcam.seal(expiry, SLOT_1500, RecordKind.OUTCOMES, (outcome(seal.sha256, exit_day=expiry,
                 exit_reason=ExitReason.EXPIRY, exit_rests_on="ab" * 32),))  # fmt: skip
    return expiry


@pytest.mark.parametrize("file_sha, fault", [("ab" * 32, None), ("cd" * 32, DataFault.SETTLEMENT_MISMATCH)])
def test_a_settled_position_reads_its_settlement_price_and_checks_its_file(file_sha, fault):
    dashcam = WriteRefusingDashcam()
    expiry = settled_by_expiry(dashcam)
    settlements = FakeSettlementSource({("BANKNIFTY", expiry): SettlementPrice(1012.5, file_sha)})
    (path,) = reader(dashcam, settlements=settlements).closed_on(expiry).paths
    assert path.faults == ((fault,) if fault else ())
    assert path.settlement == (None if fault else 1012.5)


def test_a_settlement_not_yet_published_is_a_fault():
    dashcam = WriteRefusingDashcam()
    expiry = settled_by_expiry(dashcam)
    (path,) = reader(dashcam).closed_on(expiry).paths
    assert path.faults == (DataFault.SETTLEMENT_MISSING,)


def test_a_session_with_no_outcome_file_gives_nothing():
    assert reader(WriteRefusingDashcam()).closed_on(SESSIONS[0]).paths == ()


@pytest.mark.parametrize("entered", [Outcome.NO_TRADE, Outcome.TICKET])
def test_an_outcome_whose_decision_was_not_its_kind_of_entry_is_a_fault(entered):
    dashcam = WriteRefusingDashcam()
    seal = dashcam.seal(SESSIONS[0], SLOT_1500, RecordKind.DECISIONS, (decision_record(SESSIONS[0], outcome=entered),))
    dashcam.seal(SESSIONS[0], SLOT_1500, RecordKind.OUTCOMES, (outcome(seal.sha256, exit_day=SESSIONS[0]),))
    (path,) = reader(dashcam).closed_on(SESSIONS[0]).paths
    assert path.entry is None and DataFault.ENTRY_DECISION_MISSING in path.faults


def test_a_held_session_whose_file_has_no_record_for_the_road_is_a_fault_not_a_closure():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam)
    key = (SESSIONS[1], SLOT_1500, RecordKind.DECISIONS)
    del dashcam.files[key]
    dashcam.seal(*key, (replace(decision_record(SESSIONS[1], OTHER), road=OTHER_ROAD, decision=replace(
        decision_record(SESSIONS[1], OTHER).decision, road=OTHER_ROAD)),))  # fmt: skip
    (path,) = reader(dashcam).closed_on(SESSIONS[2]).paths
    assert DataFault.SNAPSHOT_MISSING in path.faults and path.sessions_skipped == 0


def test_a_trading_session_held_without_a_sealed_decisions_file_is_a_fault():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam)
    del dashcam.files[(SESSIONS[1], SLOT_1500, RecordKind.DECISIONS)]
    (path,) = reader(dashcam).closed_on(SESSIONS[2]).paths
    assert path.faults == (DataFault.SESSION_NOT_SEALED,)


def test_a_weekend_inside_the_hold_is_not_a_session():
    dashcam = WriteRefusingDashcam()
    friday, monday = date(2026, 11, 6), date(2026, 11, 9)
    seal = dashcam.seal(friday, SLOT_1500, RecordKind.DECISIONS, (decision_record(friday),))
    dashcam.seal(monday, SLOT_1500, RecordKind.DECISIONS, (decision_record(monday, OTHER), exit_of(monday)))
    dashcam.seal(monday, SLOT_1500, RecordKind.OUTCOMES, (outcome(seal.sha256, friday, monday),))
    archive = FakeSnapshotArchive({(ROAD, d): snap(d) for d in (friday, monday)})
    (path,) = reader(dashcam, archive).closed_on(monday).paths
    assert path.attributable and [s.session for s in path.snapshots] == [friday, monday]


def exit_of(day: date, **changes) -> ExitRecord:
    values = dict(session=day, slot=SLOT_1500, position_id="p1", driver_id=DRIVER, road=ROAD,
                  exit_reason=ExitReason.PROFIT_TARGET, snapshot_id="x")  # fmt: skip
    return ExitRecord(**{**values, **changes})


@pytest.mark.parametrize("record, fault", [
    (None, DataFault.EXIT_RECORD_MISSING),
    (exit_of(SESSIONS[0], exit_reason=ExitReason.LOSS_LIMIT), DataFault.EXIT_RECORD_MISMATCH),
    (exit_of(SESSIONS[0], driver_id=OTHER), DataFault.EXIT_RECORD_MISMATCH),
    (exit_of(SESSIONS[0]), None),
])  # fmt: skip
def test_an_exit_rule_close_needs_its_own_exit_record(record, fault):
    dashcam = WriteRefusingDashcam()
    extra = (record,) if record else ()
    seal = dashcam.seal(SESSIONS[0], SLOT_1500, RecordKind.DECISIONS, (decision_record(SESSIONS[0]),) + extra)
    dashcam.seal(SESSIONS[0], SLOT_1500, RecordKind.OUTCOMES, (outcome(seal.sha256, exit_day=SESSIONS[0]),))
    (path,) = reader(dashcam).closed_on(SESSIONS[0]).paths
    assert path.faults == ((fault,) if fault else ())


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


def test_an_exit_day_closed_for_the_road_is_a_missing_snapshot():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam)
    key = (SESSIONS[2], SLOT_1500, RecordKind.DECISIONS)
    records = [r for r in FakeDashcam.read(dashcam, dashcam.find(*key)) if not isinstance(r, DecisionRecord)]
    del dashcam.files[key]
    dashcam.seal(*key, (closed_record(SESSIONS[2], OTHER), *records))
    (path,) = reader(dashcam).closed_on(SESSIONS[2]).paths
    assert DataFault.SNAPSHOT_MISSING in path.faults and path.sessions_skipped == 1


def test_a_snapshot_with_the_right_hash_but_another_id_is_a_mismatch():
    dashcam = WriteRefusingDashcam()
    held_trade(dashcam)
    archive = FakeSnapshotArchive({(ROAD, d): snap(d) for d in SESSIONS})
    archive.snapshots[(ROAD, SESSIONS[1])] = replace(snap(SESSIONS[1]), snapshot_id="other_id")
    (path,) = reader(dashcam, archive).closed_on(SESSIONS[1 + 1]).paths
    assert path.faults == (DataFault.SNAPSHOT_HASH_MISMATCH,)
