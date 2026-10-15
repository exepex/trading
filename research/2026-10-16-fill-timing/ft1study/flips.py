"""The flip share's P&L (PROTOCOL.md section 14): one lot held to expiry and settled at intrinsic value against the
final settlement price, net of C1 charges, each leg's order charged at its own entry price. A P&L of exactly zero is not
a win. Only the two flip shares leave this study; a P&L, a win rate or a count of wins never does."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from fno.constants import SIDE_BUY, SIDE_SELL
from fno.costs import order_charges, settlement_charges_breakdown
from fno.research_engine.structures import Leg, position_value, terminal_value


def settled_pnl(legs: Sequence[Leg], prices: Sequence[float], settlement: float, lot: int, charges: dict) -> float:
    gross = (terminal_value(legs, settlement) - position_value(legs, prices)) * lot
    return gross - sum(_leg_charges(leg, price, settlement, lot, charges) for leg, price in zip(legs, prices))


def _leg_charges(leg: Leg, price: float, settlement: float, lot: int, charges: dict) -> float:
    """The leg's entry order at its own price, then its settlement (closing side: sell a bought leg, buy a sold one)."""
    opening, closing = (SIDE_BUY, SIDE_SELL) if leg.bought else (SIDE_SELL, SIDE_BUY)
    settled = settlement_charges_breakdown(leg.intrinsic(settlement), lot, closing, charges)
    return order_charges(price, lot, opening, charges) + sum(settled.values())


@dataclass(frozen=True)
class FlipCounts:
    wins: int = 0  # wins at the decision price
    bad: int = 0  # of those, not a win at the fill price
    losses: int = 0  # not a win at the decision price
    good: int = 0  # of those, a win at the fill price

    def add(self, at_decision: float, at_fill: float) -> FlipCounts:
        won, still = at_decision > 0, at_fill > 0
        return FlipCounts(self.wins + won, self.bad + (won and not still), self.losses + (not won),
                          self.good + (not won and still))  # fmt: skip
