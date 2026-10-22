"""The path reader (story MS-INS, part a): every trade and ticket whose outcome was sealed on a session, joined to the
sealed decision it rests on, its exit record and the road's verified snapshot on each trading session it was held.
Reads only; whatever cannot be verified becomes a `DataFault` on the path, never a guess.

A correction is sealed on a later session than its original (each dashcam file is written once), so the original is
read on its own session and the correction on its own. `closed_between` reads a range and keeps only the latest of
each: the one view the review counts."""

import hashlib
from collections.abc import Iterable
from datetime import date

from ...models import IST
from ...research_data.calendar import SessionCalendar
from ...storage.trading_days import is_trading_day
from ..constants import SLOT_1500, ExitReason, Outcome, RecordKind
from ..contracts.accounts import IndexSettlementSource, SettlementUnavailable
from ..contracts.dashcam import DashcamStore
from ..contracts.records import DecisionRecord, ExitRecord, OutcomeRecord
from ..contracts.roads import ROADS_BY_CODE
from ..contracts.slot_file import SlotRecord
from ..contracts.snapshot import SlotSnapshot
from .contracts import DataFault, HeldPath
from .ports import SnapshotArchive


def record_sha256(record: OutcomeRecord) -> str:
    return hashlib.sha256(record.to_bytes()).hexdigest()


def latest_outcomes(outcomes: Iterable[OutcomeRecord]) -> tuple[OutcomeRecord, ...]:
    """The outcomes given, each corrected one replaced by its correction (the original stays on file)."""
    outcomes = tuple(outcomes)
    corrected = {r.corrects for r in outcomes if r.corrects}
    return tuple(r for r in outcomes if record_sha256(r) not in corrected)


class PathReader:
    def __init__(self, dashcam: DashcamStore, snapshots: SnapshotArchive, settlements: IndexSettlementSource,
                 calendar: SessionCalendar):  # fmt: skip
        self.dashcam, self.snapshots, self.settlements, self.calendar = dashcam, snapshots, settlements, calendar

    def closed_on(self, session: date) -> tuple[HeldPath, ...]:
        return tuple(self._path(outcome) for outcome in latest_outcomes(self._outcomes(session)))

    def closed_between(self, first: date, last: date) -> tuple[HeldPath, ...]:
        """Every outcome sealed from `first` to `last`, a correction replacing the original it names."""
        days = [d for d in self.calendar.sessions(first, last) if is_trading_day(self.calendar, d)]
        return tuple(self._path(o) for o in latest_outcomes(o for d in days for o in self._outcomes(d)))

    def _outcomes(self, session: date) -> tuple[OutcomeRecord, ...]:
        return tuple(r for r in self._records(session, RecordKind.OUTCOMES) or () if isinstance(r, OutcomeRecord))

    def _records(self, session: date, kind: RecordKind) -> tuple[SlotRecord, ...] | None:
        seal = self.dashcam.find(session, SLOT_1500, kind)
        return None if seal is None else self.dashcam.read(seal)

    def _path(self, outcome: OutcomeRecord) -> HeldPath:
        entry_day, exit_day = _ist_day(outcome.entry.filled_at), _ist_day(outcome.exit.filled_at)
        faults: list[DataFault] = []
        entry = self._entry(outcome, entry_day, faults)
        snapshots, skipped, exit_record = [], 0, None
        for day in (d for d in self.calendar.sessions(entry_day, exit_day) if is_trading_day(self.calendar, d)):
            records = self._records(day, RecordKind.DECISIONS)
            if records is None:
                faults.append(DataFault.SESSION_NOT_SEALED)
                continue
            snapshot, closed = self._snapshot(outcome, day, records, faults)
            skipped += closed
            snapshots += [snapshot] if snapshot else []
            exit_record = exit_record or _exit_record(outcome, records)
        settled = outcome.exit_reason == ExitReason.EXPIRY
        if not snapshots or snapshots[0].session != entry_day or (not settled and snapshots[-1].session != exit_day):
            faults.append(DataFault.SNAPSHOT_MISSING)
        if not settled:
            _check_exit(outcome, exit_record, faults)
        settlement = self._settlement(outcome, exit_day, faults) if settled else None
        unique = tuple(dict.fromkeys(faults))
        return HeldPath(outcome, entry, exit_record, tuple(snapshots), settlement, skipped, unique)

    def _entry(self, outcome: OutcomeRecord, day: date, faults: list[DataFault]) -> DecisionRecord | None:
        seal = self.dashcam.find(day, SLOT_1500, RecordKind.DECISIONS)
        records = self.dashcam.read(seal) if seal else ()
        wanted = Outcome.TICKET if outcome.is_ticket else Outcome.TRADE
        mine = (r for r in records if isinstance(r, DecisionRecord) and r.road == outcome.road)
        entry = next(
            (r for r in mine if (r.decision.driver_id, r.decision.outcome) == (outcome.driver_id, wanted)), None
        )
        if entry is None:
            faults.append(DataFault.ENTRY_DECISION_MISSING)
        elif seal.sha256 != outcome.decision_sha256:
            faults.append(DataFault.ENTRY_SEAL_MISMATCH)
        return entry

    def _snapshot(self, outcome, day, records, faults) -> tuple[SlotSnapshot | None, bool]:
        """The session's verified snapshot, or None; True when a sealed closure of the road explains its absence."""
        on_road = [r for r in records if isinstance(r, DecisionRecord) and r.road == outcome.road]
        named = next((r for r in on_road if r.snapshot_sha256), None)
        if named is None:
            closed = any(r.road_closed_by is not None for r in on_road)
            if not closed:
                faults.append(DataFault.SNAPSHOT_MISSING)
            return None, closed  # a closed road: its step merges with the next
        snapshot = self.snapshots.snapshot(outcome.road, day)
        if snapshot is None:
            faults.append(DataFault.SNAPSHOT_MISSING)
        elif (snapshot.sha256, snapshot.snapshot_id) != (named.snapshot_sha256, named.snapshot_id):
            faults.append(DataFault.SNAPSHOT_HASH_MISMATCH)
        else:
            return snapshot, False
        return None, False

    def _settlement(self, outcome: OutcomeRecord, expiry: date, faults: list[DataFault]) -> float | None:
        try:
            final = self.settlements.price(ROADS_BY_CODE[outcome.road].underlying, expiry)
        except SettlementUnavailable:
            faults.append(DataFault.SETTLEMENT_MISSING)
            return None
        if final.file_sha256 != outcome.exit.rests_on:
            faults.append(DataFault.SETTLEMENT_MISMATCH)
            return None
        return final.price


def _ist_day(at) -> date:
    return at.astimezone(IST).date()


def _exit_record(outcome: OutcomeRecord, records: tuple[SlotRecord, ...]) -> ExitRecord | None:
    return next((r for r in records if isinstance(r, ExitRecord) and r.position_id == outcome.position_id), None)


def _check_exit(outcome: OutcomeRecord, record: ExitRecord | None, faults: list[DataFault]) -> None:
    """An exit rule's close leaves an exit record (story 3.4): causes 6 and 11 read it."""
    if record is None:
        faults.append(DataFault.EXIT_RECORD_MISSING)
    elif (record.driver_id, record.road, record.exit_reason) != (outcome.driver_id, outcome.road, outcome.exit_reason):
        faults.append(DataFault.EXIT_RECORD_MISMATCH)
