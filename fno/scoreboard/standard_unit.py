"""Scoreboard A's standard unit (story S3; S1 `scoreboard_a_standardisation`), the one valuation F9 also imports: one
lot of each leg, entered at a day's execution snapshot by E4's pricing (the touch, all units or none) with C1's charges,
and exited by the version's time exit at that session's snapshot. A leg without a valid quote then is retried at each
next snapshot (E4's rule), dated the day it fills; a leg still open after its expiry is settled at E7's final
settlement price. No price is invented: an entry leg that does not fill leaves the unit "not filled"."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from ..constants import NIFTY_SYMBOL, SIDE_BUY
from ..costs import order_charges, settlement_charges_breakdown
from ..desk.pricing import DeskLeg, price_leg
from ..desk.settlement import SettlementPrices
from ..desk.snapshot import ExecutionSnapshot
from ..risk.inputs import RiskInputError
from ..risk.open_risk import HeldMaxLoss

CLOSED, OPEN, NOT_FILLED, MAX_LOSS_UNKNOWN = "closed", "open", "not filled", "maximum loss unknown"

Snapshots = Callable[[date], ExecutionSnapshot | None]  # a day's valid execution snapshot, None when there is none
SessionsBetween = Callable[[date, date], Sequence[date]]  # the sessions from the first day to the last, both included


@dataclass(frozen=True)
class StandardResult:
    status: str
    net: float | None = None  # rupees, every charge included; only when closed
    max_loss: float | None = None  # B2's model on the one-lot entry fills (story S3: never the record's figure)
    exited_on: date | None = None
    note: str = ""


def cash(price: float, side: str, units: int, charges: Mapping[str, float]) -> float:
    """What one fill moves: premium received for a sale, paid for a purchase, less the order's charges."""
    sign = -1 if side == SIDE_BUY else 1
    return sign * price * units - order_charges(price, units, side, dict(charges))


class StandardUnit:
    def __init__(self, snapshots: Snapshots, sessions: SessionsBetween, settlements: SettlementPrices,
                 held: HeldMaxLoss, charges: Mapping[str, float], lot: int):  # fmt: skip
        self.snapshots, self.sessions, self.settlements = snapshots, sessions, settlements
        self.held, self.charges, self.lot = held, dict(charges), lot

    def value(self, legs: Sequence[DeskLeg], entry_day: date, exit_day: date, on: date) -> StandardResult:
        """The one-lot unit entered on `entry_day`, as known on `on`."""
        snapshot = self.snapshots(entry_day)
        quotes = [price_leg(snapshot, leg, leg.side(True), self.lot) for leg in legs] if snapshot else []
        missing = [q for q in quotes if not q.fills]
        if snapshot is None or missing:
            reason = "no valid execution snapshot" if snapshot is None else missing[0].reason
            return StandardResult(NOT_FILLED, note=reason)
        flow = sum(cash(q.price, q.side, self.lot, self.charges) for q in quotes)
        try:
            max_loss = self.held.of_legs([(leg.leg, self.lot) for leg in legs], flow)
        except RiskInputError as problem:
            return StandardResult(MAX_LOSS_UNKNOWN, note=str(problem))
        return self._exit(list(legs), flow, max_loss, exit_day, on)

    def _exit(self, legs: list[DeskLeg], flow: float, max_loss: float, exit_day: date, on: date) -> StandardResult:
        last = None
        for day in self.sessions(exit_day, on) if exit_day <= on else ():
            snapshot = self.snapshots(day)
            for leg in [leg for leg in legs if snapshot is not None and day <= leg.expiry]:
                quote = price_leg(snapshot, leg, leg.side(False), self.lot)
                if quote.fills:
                    flow, last = flow + cash(quote.price, quote.side, self.lot, self.charges), day
                    legs.remove(leg)
        for leg in [leg for leg in legs if leg.expiry < on]:
            final = self.settlements.final_settlement(NIFTY_SYMBOL, leg.expiry)
            if final is None:
                continue
            flow, last = flow + self._settled(leg, final.price), max(last or leg.expiry, leg.expiry)
            legs.remove(leg)
        if legs:
            return StandardResult(OPEN, max_loss=max_loss, note=f"{len(legs)} leg(s) still open")
        return StandardResult(CLOSED, round(flow, 2), round(max_loss, 2), last)

    def _settled(self, leg: DeskLeg, price: float) -> float:
        intrinsic, side = leg.leg.intrinsic(price), leg.side(False)
        sign = -1 if side == SIDE_BUY else 1
        charges = sum(settlement_charges_breakdown(intrinsic, self.lot, side, self.charges).values())
        return sign * intrinsic * self.lot - charges
