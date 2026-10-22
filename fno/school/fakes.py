"""In-memory fakes of every school port (story MS-P1a), for the parts' tests. Each passes the conformance checks in
`tests/school/contracts/conformance.py`, as every real class must. No production path imports this module."""

import hashlib
from dataclasses import dataclass, field, replace
from datetime import date, datetime

from ..constants import SIDE_BUY, SIDE_SELL
from .constants import ClosureReason, ExitState, NoTradeReason, Outcome, RefusalReason
from .contracts.accounts import FilledLeg, FillResult
from .contracts.dashcam import ReplayConflict, Seal, StaleSeal
from .contracts.decisions import Decision, DriverCard, OpenPosition, Proposal, SpotPoint
from .contracts.reports import Banner, SectionText
from .contracts.roads import RoadDay
from .contracts.safety import AccountView, LawResult
from .contracts.snapshot import SlotSnapshot, SnapshotUnavailable


@dataclass
class FakeRoadCatalogue:
    days: dict[date, tuple[RoadDay, ...]] = field(default_factory=dict)

    def day(self, session: date) -> tuple[RoadDay, ...]:
        return self.days.get(session, ())


@dataclass
class FakeSnapshotSource:
    snapshots: dict[tuple, SlotSnapshot] = field(default_factory=dict)  # (road code, session) -> snapshot

    def for_road(self, road_day: RoadDay) -> SlotSnapshot:
        if not road_day.status.open:
            raise SnapshotUnavailable(road_day.status.closed_by)
        found = self.snapshots.get((road_day.road.code, road_day.session))
        if found is None:
            raise SnapshotUnavailable(ClosureReason.CAPTURE_MISSING)
        return found


@dataclass
class FakeDriver:
    """Proposes its scripted proposal on every road, or no trade when it has none."""

    card: DriverCard
    proposal: Proposal | None = None

    def decide(self, road_day: RoadDay, snapshot: SlotSnapshot, history: tuple[SpotPoint, ...],
               positions: tuple[OpenPosition, ...]) -> Decision:  # fmt: skip
        road, session = road_day.road.code, road_day.session
        if self.proposal is None:
            return Decision(self.card.driver_id, road, session, Outcome.NO_TRADE, NoTradeReason.RULE_NOT_FIRED)
        return Decision(self.card.driver_id, road, session, Outcome.TRADE, "", self.proposal)


@dataclass
class FakeMaxLossLaw:
    limit: float
    name: str = "max_loss"

    def check(self, proposal: Proposal, account: AccountView, snapshot: SlotSnapshot, session: date) -> LawResult:
        passed = proposal.max_loss <= self.limit
        return LawResult(self.name, passed, None if passed else RefusalReason.MAX_LOSS, self.limit, proposal.max_loss)


@dataclass
class FakeAccounts:
    capital: float
    ledgers: dict[str, list[FillResult]] = field(default_factory=dict)

    def view(self, driver_id: str, snapshot: SlotSnapshot) -> AccountView:
        cash = self.capital + sum(_cash(r) for r in self.ledgers.get(driver_id, []))
        return AccountView(driver_id, self.capital, cash, cash, max(cash, self.capital), 0.0, (), (), None)

    def record(self, driver_id: str, result: FillResult) -> None:
        if result.filled:
            self.ledgers.setdefault(driver_id, []).append(result)


def _cash(result: FillResult) -> float:
    return sum((leg.price if leg.side == SIDE_SELL else -leg.price) * leg.units - leg.charges for leg in result.legs)


@dataclass
class FakeFills:
    """Fills every leg at the touch when the seal was pushed by `fill_time` and every quote is two-sided; refuses
    otherwise. Charges are zero."""

    fill_time: datetime

    def enter(self, decision: Decision, snapshot: SlotSnapshot, seal: Seal) -> FillResult:
        if not seal.covers(seal.sha256, self.fill_time):
            return FillResult(refused=(RefusalReason.STALE_SEAL,))
        legs = []
        for leg in decision.proposal.legs:
            quote = snapshot.quote(leg.key)
            if quote is None or not quote.two_sided:
                return FillResult(refused=(RefusalReason.MISSING_QUOTE,))
            price = quote.ask if leg.side == SIDE_BUY else quote.bid
            legs.append(FilledLeg(leg.key, leg.side, leg.lots * decision.proposal.lot, price, 0.0))
        return FillResult(tuple(legs), filled_at=self.fill_time, seal_sha256=seal.sha256)

    def exit(self, position: OpenPosition, snapshot: SlotSnapshot, reason: str, seal: Seal) -> FillResult:
        flip = {SIDE_BUY: SIDE_SELL, SIDE_SELL: SIDE_BUY}
        reversed_legs = tuple(replace(leg, side=flip[leg.side]) for leg in position.legs)
        closing = Proposal("close", reversed_legs, position.lot, 0.0, position.max_loss, 0.0)
        decision = Decision(position.driver_id, position.road, snapshot.session, Outcome.TRADE, "", closing)
        return self.enter(decision, snapshot, seal)

    def settle(self, position: OpenPosition, expiry: date) -> FillResult:
        return FillResult(state=ExitState.SETTLEMENT_NEEDED)


@dataclass
class FakeDashcam:
    files: dict[str, bytes] = field(default_factory=dict)
    pushed_at: datetime | None = None  # the fake's push time; None means "now is the session's 15:00 slot"

    def seal(self, session: date, slot: str, payload: bytes) -> Seal:
        path = f"school/dashcam/{session:%Y/%m/%d}/{slot.replace(':', '')}.jsonl.gz"
        if path in self.files and self.files[path] != payload:
            raise ReplayConflict(path)
        self.files[path] = payload
        digest = hashlib.sha256(payload).hexdigest()
        when = self.pushed_at or datetime.fromisoformat(f"{session}T{slot}:00+05:30")
        return Seal(path, digest, when, "fake")

    def read(self, seal: Seal) -> bytes:
        data = self.files.get(seal.path)
        if data is None or hashlib.sha256(data).hexdigest() != seal.sha256:
            raise StaleSeal(seal.path)
        return data


@dataclass
class FakeSection:
    title: str = "Today"

    def render(self, session: date) -> SectionText:
        return SectionText(self.title, (f"{session}",), Banner.AMBER)
