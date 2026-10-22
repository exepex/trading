"""The quality gate of a road-day (story 3.5): the snapshot a driver is about to see is the one the road said it was,
and its quotes can be priced. A closed road stays closed with its one reason; an open one closes with exactly one."""

from dataclasses import dataclass

from ..constants import ClosureReason
from ..contracts.roads import OPEN, RoadDay, RoadStatus
from ..contracts.snapshot import SlotSnapshot
from .band import DEFAULT_BAND_STEPS, band_keys
from .prices import impossible_keys
from .rules import expiry_problem, window_problem

WRONG_SNAPSHOT = "the snapshot is not the road-day's own: {snapshot} against {road_day}"


@dataclass(frozen=True)
class LegCounts:
    """The scheduled leg observations of one road-session and how many counted (valid, two-sided, not impossible)."""

    observed: int
    passed: int


class RoadQualityGate:
    def __init__(self, band_steps: int = DEFAULT_BAND_STEPS):
        self.band_steps = band_steps

    def check(self, road_day: RoadDay, snapshot: SlotSnapshot) -> RoadStatus:
        """Open, or closed with the first reason found: out of window, expiry mismatch, impossible price. A road the
        catalogue closed keeps its reason."""
        if not road_day.status.open:
            return road_day.status
        if (snapshot.road, snapshot.session) != (road_day.road.code, road_day.session):
            raise ValueError(WRONG_SNAPSHOT.format(snapshot=(snapshot.road, snapshot.session),
                                                   road_day=(road_day.road.code, road_day.session)))  # fmt: skip
        reason = (
            window_problem(snapshot.road, snapshot.session, snapshot.started_at, snapshot.finished_at)
            or expiry_problem(snapshot.expiries, road_day.expiries)
            or (ClosureReason.IMPOSSIBLE_PRICE if self._impossible_in_band(road_day, snapshot) else None)
        )
        return RoadStatus(reason) if reason else OPEN

    def legs(self, road_day: RoadDay, snapshot: SlotSnapshot) -> LegCounts:
        """The band's leg observations of an open road-day."""
        keys = self._band(road_day, snapshot)
        impossible = impossible_keys(snapshot, keys)
        passed = sum(1 for key in keys if snapshot.quotes[key].two_sided and key not in impossible)
        return LegCounts(len(keys), passed)

    def _impossible_in_band(self, road_day: RoadDay, snapshot: SlotSnapshot) -> bool:
        return bool(impossible_keys(snapshot, self._band(road_day, snapshot)))

    def _band(self, road_day: RoadDay, snapshot: SlotSnapshot):
        return band_keys(snapshot, road_day.strike_step, self.band_steps)
