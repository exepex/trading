"""One recorded session as plain data (story MS-P1i): the roads, their snapshots, the drivers' scripted proposals and
the timing of the seal. The harness builds a fleet from it (the fake fleet here, the real wiring in MS-P1j) and a
fault planter returns a changed copy. Data only: no port, no clock, no production path."""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import date, datetime

from ..constants import ClosureReason, RoadCode
from ..contracts.decisions import DriverCard, Proposal
from ..contracts.roads import RoadDay, RoadStatus
from ..contracts.snapshot import ContractKey, SlotSnapshot


@dataclass(frozen=True)
class DriverPlan:
    """A driver that proposes `proposal` on every open road (no trade when None)."""

    card: DriverCard
    proposal: Proposal | None = None


@dataclass(frozen=True)
class Scenario:
    session: date
    road_days: tuple[RoadDay, ...]
    snapshots: Mapping[RoadCode, SlotSnapshot]
    drivers: tuple[DriverPlan, ...]
    cap_rs: float  # the per-trade maximum loss the laws enforce
    fill_at: datetime  # when the fleet fills
    seal_pushed_at: datetime  # when the decisions file's receipt reaches the remote

    @property
    def scheduled(self) -> set[tuple[RoadCode, str]]:
        """Every scheduled road decision: (road, driver id), one per road and driver version."""
        return {(day.road.code, plan.card.driver_id) for day in self.road_days for plan in self.drivers}

    def road_day(self, road: RoadCode) -> RoadDay:
        return next(day for day in self.road_days if day.road.code == road)

    def with_road_closed(self, road: RoadCode, reason: ClosureReason) -> "Scenario":
        closed = replace(self.road_day(road), expiries=(), lot=None, strike_step=None, status=RoadStatus(reason))
        return replace(self, road_days=tuple(closed if d.road.code == road else d for d in self.road_days))

    def without_quote(self, road: RoadCode, key: ContractKey) -> "Scenario":
        snapshot = self.snapshots[road]
        quotes = {k: q for k, q in snapshot.quotes.items() if k != key}
        return replace(self, snapshots={**self.snapshots, road: replace(snapshot, quotes=quotes)})

    def with_plan(self, plan: DriverPlan) -> "Scenario":
        """Adds a driver, or replaces the one with the same driver id."""
        kept = tuple(p for p in self.drivers if p.card.driver_id != plan.card.driver_id)
        return replace(self, drivers=(*kept, plan))
