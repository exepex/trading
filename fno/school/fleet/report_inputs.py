"""What g's two sections read (story MS-P1g's ports, wired by MS-P1j): the session's sealed records from the dashcam,
the three counts from the session's committed counts file, each driver's role from its card, and the session's roads
from the catalogue. Nothing here decides; it only reads what the run sealed and committed."""

import csv
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Protocol

from ..constants import SLOT_1500, DriverRole, Outcome, RecordKind, RoadCode
from ..contracts.dashcam import DashcamStore
from ..contracts.roads import RoadCatalogue, RoadDay
from ..contracts.slot_file import SlotRecord
from ..contracts.tickets import OpportunityCounts
from ..reports.inputs import PlannedTrade
from .counts_file import SessionCounts, opportunity_path
from .isolate import isolated
from .slot import plan_slot


class WhyLines(Protocol):
    def lines(self, session: date) -> tuple[str, ...]: ...


class SealedDayInputs:
    def __init__(self, dashcam: DashcamStore, root: Path, roles: Mapping[str, DriverRole], why: WhyLines | None = None):
        """`why`: MS-INS part e's line per closed trade (driver, road, net and cause words; never a contract)."""
        self.dashcam, self.root, self.roles, self.why_lines = dashcam, Path(root), dict(roles), why

    def records(self, session: date) -> tuple[SlotRecord, ...]:
        found = []
        for kind in (RecordKind.DECISIONS, RecordKind.OUTCOMES):
            seal = self.dashcam.find(session, SLOT_1500, kind)
            found.extend(self.dashcam.read(seal) if seal is not None else ())
        return tuple(found)

    def counts(self, session: date) -> tuple[OpportunityCounts, ...]:
        file = self.root / opportunity_path(session, SLOT_1500)
        if not file.is_file():
            return ()
        with file.open() as rows:
            return tuple(OpportunityCounts(date.fromisoformat(r["session"]), RoadCode(r["road"]), r["driver"],
                                           int(r["eligible"]), int(r["fillable"]), int(r["executed"]))
                         for r in csv.DictReader(rows))  # fmt: skip

    def role_of(self, driver_id: str) -> DriverRole:
        return self.roles[driver_id]

    def why(self, session: date) -> tuple[str, ...]:
        return () if self.why_lines is None else tuple(self.why_lines.lines(session))

    def marks(self, session: date) -> tuple[str, ...]:
        return SessionCounts(self.root, None).marks(session, SLOT_1500)


class PreviousSlotToday:
    """The 08:50 section's inputs (325 9.21, "plan at 08:50, booking at the slot"): today's captures do not
    exist yet, so the roads are the previous session's 15:00 roads and the plan is what each rule driver's card proposes
    on that slot's snapshots. It is indicative: no law runs, nothing is sealed, nothing is booked. Each trade is booked
    at today's slot at today's quotes, or dropped with its reason, and the 20:05 section shows what was booked. Each
    driver is isolated as at the slot, and a failing one simply plans nothing."""

    def __init__(self, calendar, catalogue: RoadCatalogue, snapshots, gate, drivers, history, seconds: float = 60.0):
        self.calendar, self.catalogue, self.snapshots, self.gate = calendar, catalogue, snapshots, gate
        self.drivers, self.history, self.seconds = drivers, history, seconds

    def roads(self, session: date) -> tuple[RoadDay, ...]:
        return self.catalogue.day(self.source(session))

    def source(self, session: date) -> date:
        return self.calendar.previous_session(session)

    def plan(self, session: date) -> tuple[PlannedTrade, ...]:
        previous = self.source(session)
        slot = plan_slot(previous, self.catalogue, self.snapshots, self.gate)
        planned = []
        for driver in (d for d in self.drivers if d.card.role is DriverRole.RULE):
            done = isolated(lambda d=driver: self._proposals(d, slot, previous), self.seconds)
            planned.extend(done.value or ())
        return tuple(planned)

    def _proposals(self, driver, slot, previous: date) -> list[PlannedTrade]:
        trades = []
        for road in slot.open:
            code = road.road_day.road.code
            history = self.history.spots(road.road_day.road, previous)
            decision = driver.decide(road.road_day, road.snapshot, history, ())
            if decision.outcome == Outcome.TRADE:
                p = decision.proposal
                trades.append(PlannedTrade(driver.card.driver_id, driver.card.role, code, p.structure, p.max_loss))
        return trades
