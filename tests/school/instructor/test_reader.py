"""Part a's path reader (story MS-INS, criteria 1-5): closed trades and tickets joined to their sealed decision, exit
record and verified snapshots; every unverifiable input a data fault, never a guess. Criterion 5 (reads only): the
dashcam below refuses any write once the fixtures are laid, and every other port the reader holds has no write method;
the whole instructor run is checked on the fake fleet again when part e joins the parts."""

from dataclasses import replace
from datetime import date

import pytest

from fno.school.constants import SLOT_1500, ExitReason, Outcome, RecordKind
from fno.school.contracts.accounts import SettlementPrice
from fno.school.contracts.records import DecisionRecord, ExitRecord
from fno.school.fakes import FakeDashcam, FakeSettlementSource
from fno.school.instructor.contracts import DataFault
from fno.school.instructor.fakes import FakeSnapshotArchive
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
from tests.school.instructor.reading import OTHER_ROAD, WriteRefusingDashcam, reader


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
