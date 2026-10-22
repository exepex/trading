"""One driver at the slot (story MS-P1j; order: drivers, laws, then the exit reviews), isolated as one unit:
- only the card's own roads are scheduled for the driver (its `roads`; CARD_P1 section 1): each open one gets the
  driver's decision on its snapshot and its own earlier spots, each closed one a sealed `road_closed` with the road's
  reason;
- the driver decides on the account's own positions only, so a virtual ticket never blocks a real entry; the fired
  trades go through `tickets.rules.classify`, whose law check sees the slot's running view (the trades already
  accepted), so the slot's caps add up before any fill;
- a ticket is the hypothetical account without the account limits, holding the real positions and the open tickets:
  on a road where the driver already holds a ticket, the card is asked again with both, and when it would not trade
  there (its own "already holding" rule) no second ticket is made; its record is that decision (orchestrator's
  ruling d, 22 Oct 2026);
- each open position the driver holds on an open road gets the card's exit review, after the pairing check: a
  position of another driver is a wiring fault, and the driver's whole slot is `unavailable: driver_error`, never an
  exit.
Any exception, or the time limit, seals every road of the driver `unavailable`, with no exit."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from ..constants import SLOT_1500, Outcome, RoadCode
from ..contracts.decisions import Decision, Driver, OpenPosition, SpotPoint
from ..contracts.records import DecisionRecord, ExitRecord
from ..contracts.roads import ROADS
from ..contracts.safety import AccountView, LawResult
from ..tickets.rules import classify
from .isolate import isolated
from .records import closed_record, decision_record, unavailable
from .running_view import running_view
from .slot import SlotRoads

LawCheck = Callable[..., tuple[LawResult, ...]]  # SafetyLaws.check(proposal, account, snapshot, session)
History = Callable[[RoadCode], tuple[SpotPoint, ...]]


ROAD_ORDER = {road.code: index for index, road in enumerate(ROADS)}


class PairingError(RuntimeError):
    """A position offered for a driver's exit review is not that driver's, or not of an open road of this slot."""


@dataclass(frozen=True)
class DriverSlot:
    records: tuple[DecisionRecord, ...]  # one per scheduled road, in the catalogue's order
    exits: tuple[ExitRecord, ...]


@dataclass(frozen=True)
class DriverStep:
    laws: LawCheck
    history: History
    max_new: int
    seconds: float

    def run(self, driver: Driver, roads: SlotRoads, view: AccountView, held: tuple[OpenPosition, ...],
            tickets: tuple[OpenPosition, ...]) -> DriverSlot:  # fmt: skip
        """`view`: the account at the slot (after settlement); `held` its open positions; `tickets` the driver's open
        tickets, reviewed by the same card."""
        card = driver.card
        roads = roads.only(card.roads)
        closed = tuple(closed_record(card, road) for road in roads.closed)
        if not roads.open:
            return DriverSlot(_in_order(roads, closed), ())  # nothing to decide or review on this slot
        done = isolated(lambda: self._open_roads(driver, roads, view, held, tickets), self.seconds)
        if done.failed:
            failed = tuple(decision_record(card, unavailable(card, r.road_day, done.failed), r.snapshot, (),
                                           len(self.history(r.road_day.road.code)), done.error_class)
                           for r in roads.open)  # fmt: skip
            return DriverSlot(_in_order(roads, failed + closed), ())
        records, exits = done.value
        return DriverSlot(_in_order(roads, records + closed), exits)

    def _open_roads(self, driver: Driver, roads: SlotRoads, view: AccountView, held: tuple[OpenPosition, ...],
                    tickets: tuple[OpenPosition, ...]):  # fmt: skip
        session, card = view_session(roads), driver.card
        snapshots = roads.marks
        decided = {}
        for road in roads.open:
            decided[road.road_day.road.code] = self._ask(driver, road, held, session)
        fired = tuple(d for d in decided.values() if d.outcome == Outcome.TRADE)

        def check(decision: Decision, accepted: tuple[Decision, ...]) -> tuple[LawResult, ...]:
            return self.laws(decision.proposal, running_view(view, accepted), snapshots[decision.road], session)

        laws: dict[RoadCode, tuple[LawResult, ...]] = {}
        for final, results in classify(fired, check, self.max_new):
            if final.outcome == Outcome.TICKET and any(t.road == final.road for t in tickets):
                road = next(r for r in roads.open if r.road_day.road.code == final.road)
                again = self._ask(driver, road, (*held, *tickets), session)
                final, results = (final, results) if again.outcome == Outcome.TRADE else (again, ())
            decided[final.road], laws[final.road] = final, results
        records = tuple(decision_record(card, decided[r.road_day.road.code], r.snapshot,
                                        laws.get(r.road_day.road.code, ()), len(self.history(r.road_day.road.code)))
                        for r in roads.open)  # fmt: skip
        return records, self._exits(driver, roads, (*held, *tickets))

    def _ask(self, driver: Driver, road, positions: tuple[OpenPosition, ...], session: date) -> Decision:
        code = road.road_day.road.code
        mine = tuple(p for p in positions if p.road == code)
        decision = driver.decide(road.road_day, road.snapshot, self.history(code), mine)
        _check_identity(decision, driver.card.driver_id, code, session)
        return decision

    def _exits(self, driver: Driver, roads: SlotRoads, positions: tuple[OpenPosition, ...]) -> tuple[ExitRecord, ...]:
        exits = []
        for position in positions:
            if position.driver_id != driver.card.driver_id:
                raise PairingError(f"{position.position_id} is not {driver.card.driver_id}'s")
            road = next((r for r in roads.open if r.road_day.road.code == position.road), None)
            if road is None:
                continue  # the road is closed this slot: no quotes, no review; the position stays
            if road.snapshot.road != position.road:
                raise PairingError(f"{position.position_id} reviewed on {road.snapshot.road}'s snapshot")
            reason = driver.review_exit(position, road.snapshot, self.history(position.road))
            if reason is not None:
                exits.append(ExitRecord(road.snapshot.session, SLOT_1500, position.position_id, position.driver_id,
                                        position.road, reason, road.snapshot.snapshot_id))  # fmt: skip
        return tuple(exits)


def view_session(roads: SlotRoads) -> date:
    return roads.scheduled[0].session


def _check_identity(decision: Decision, driver_id: str, road: RoadCode, session: date) -> None:
    if (decision.driver_id, decision.road, decision.session) != (driver_id, road, session):
        raise PairingError(f"a decision for {decision.driver_id} on {decision.road} {decision.session}")


def _in_order(roads: SlotRoads, records: tuple[DecisionRecord, ...]) -> tuple[DecisionRecord, ...]:
    return tuple(sorted(records, key=lambda r: ROAD_ORDER[r.road]))
