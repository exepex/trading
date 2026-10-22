"""The fleet runner (story MS-P1j): one session of every driver on every road, in the story's order. `school.enabled`
is the only switch: off, it prints the school-off line and touches nothing.

1. Expired positions settle before the session's first account view (judge 486's note).
2. If the session's decisions file is already sealed, nothing is decided or sealed again: the fills the run did not
   finish (a crash between the seal and the fills) are made, each skipped when its ledger already holds it.
3. Otherwise: the roads and the quality gate (`plan_slot`); each driver isolated (`DriverStep`); one decisions file
   sealed with every decision and exit record before any fill; then the fills (`FillStep`).
4. The outcomes and drift files are sealed, and the counts written and committed once, by this one runner."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from ...desk.snapshot import ExecutionSnapshot
from ..constants import SCHOOL_OFF_LINE, SLOT_1500, ExitReason, RecordKind, RoadCode
from ..contracts.clock import Clock
from ..contracts.dashcam import DashcamStore
from ..contracts.decisions import Driver, SpotPoint
from ..contracts.fleet import RunMode, SessionRun
from ..contracts.records import DecisionRecord, ExitRecord
from ..contracts.roads import ROADS_BY_CODE, Road, RoadCatalogue
from ..contracts.snapshot import SlotSnapshot, SnapshotSource
from ..settings import SchoolSettings
from ..tickets.counts import counts_for
from .books import Books, EntryMids
from .counts_file import SessionCounts
from .decide import DriverStep
from .fill import FillStep, SlotFills
from .ledgers import open_positions
from .outcomes import outcomes_of
from .rerun import not_yet_filled
from .settle import settle_expired
from .slot import QualityGate, SlotRoads, plan_slot

LawsFor = Callable[[Mapping[RoadCode, SlotSnapshot]], object]  # the slot's `SafetyLaws`, built on its marks


class SpotHistory(Protocol):
    def spots(self, road: Road, session: date) -> tuple[SpotPoint, ...]: ...


@dataclass
class SchoolFleet:
    settings: SchoolSettings
    catalogue: RoadCatalogue
    snapshots: SnapshotSource
    gate: QualityGate
    history: SpotHistory
    drivers: tuple[Driver, ...]
    laws_for: LawsFor
    books: Books
    dashcam: DashcamStore
    counts: SessionCounts
    capture_1515: Callable[[date], ExecutionSnapshot | None]
    entry_mids: EntryMids
    clock: Clock
    seconds_per_driver: float = 60.0

    def run(self, session: date, mode: RunMode) -> SessionRun:
        if not self.settings.enabled:
            return SessionRun(session, mode, SCHOOL_OFF_LINE)
        roads = plan_slot(session, self.catalogue, self.snapshots, self.gate)
        if not roads.scheduled:
            return SessionRun(session, mode, "")
        found = self.dashcam.find(session, SLOT_1500, RecordKind.DECISIONS)
        if found is not None:
            records, exits = self._sealed(found)
            self._finish(roads, records, exits, found)
            return SessionRun(session, mode, "", records, found)
        settled = settle_expired(self.books, self._ids(), session)
        records, exits = self._decide(roads, session)
        seal = self.dashcam.seal(session, SLOT_1500, RecordKind.DECISIONS, (*records, *settled, *exits))
        fills = self._finish(roads, records, (*settled, *exits), seal)
        return SessionRun(session, mode, "", records, seal, fills.fills)

    def _decide(self, roads: SlotRoads, session: date) -> tuple[tuple[DecisionRecord, ...], tuple[ExitRecord, ...]]:
        laws = self.laws_for(roads.marks)
        step = DriverStep(laws.check, lambda code: self.history.spots(ROADS_BY_CODE[code], session),
                          self.settings.max_new_trades_per_slot, self.seconds_per_driver)  # fmt: skip
        records, exits = [], []
        for driver in self.drivers:
            driver_id = driver.card.driver_id
            view = self.books.accounts.view(driver_id, roads.marks, session)
            tickets = open_positions(self.books.ticket_entries.entries(driver_id))
            slot = step.run(driver, roads, view, view.open_positions, tickets)
            records.extend(slot.records)
            exits.extend(slot.exits)
        return tuple(records), tuple(exits)

    def _sealed(self, seal) -> tuple[tuple[DecisionRecord, ...], tuple[ExitRecord, ...]]:
        sealed = self.dashcam.read(seal)
        return (tuple(r for r in sealed if isinstance(r, DecisionRecord)),
                tuple(r for r in sealed if isinstance(r, ExitRecord)))  # fmt: skip

    def _ids(self) -> tuple[str, ...]:
        return tuple(d.card.driver_id for d in self.drivers)

    def _finish(self, roads, records, exits, seal) -> SlotFills:
        session = roads.scheduled[0].session
        if self.dashcam.find(session, SLOT_1500, RecordKind.OUTCOMES) is not None:
            return SlotFills({}, frozenset(), frozenset(), ())  # the session is complete
        slot_exits = tuple(e for e in exits if e.exit_reason != ExitReason.EXPIRY)
        todo, todo_exits = not_yet_filled(self.books, self._ids(), records, slot_exits)
        step = FillStep(self.books, self.capture_1515(session), self.entry_mids)
        fills = step.run(roads, todo, todo_exits, seal, self.clock.now())
        outcomes = outcomes_of(self.books, exits, roads.marks, self.entry_mids)
        self.dashcam.seal(session, SLOT_1500, RecordKind.OUTCOMES, outcomes)
        self.dashcam.seal(session, SLOT_1500, RecordKind.DRIFT, fills.drift)
        counts = tuple(counts_for(r.decision, r.law_results, fills.entries.get((r.road, r.decision.driver_id)),
                                  (r.road, r.decision.driver_id) in fills.size_shared) for r in records)  # fmt: skip
        self.counts.write(session, SLOT_1500, records, counts)
        return fills
