"""A proposal's money at entry: its modelled maximum loss and its entry cash flow (story C2).

The risk manager depends on the `TradeCosts` interface; `SimulatorTradeCosts` is the one implementation and reuses the
cycle simulator's cost model (story B2: pads, every charge from `fno.costs`, worst-case exit charges), so the risk
manager, the research and the cap agree to the rupee on what a trade can lose.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from ..research_engine.cycle_costs import PAD, CycleTerms, PositionCosts
from .inputs import Market, Proposal


class TradeCosts(Protocol):
    def max_loss(self, proposal: Proposal, market: Market) -> float:
        """The most the trade can lose in rupees, every charge and pad included."""

    def entry_cash_flow(self, proposal: Proposal, market: Market) -> float:
        """Cash the entry moves: premium received minus paid at the padded fill prices, minus entry charges."""


class SimulatorTradeCosts:
    def __init__(self, charges: Mapping[str, float], pad: float = PAD):
        self.charges, self.pad = dict(charges), pad

    def _costs(self, proposal: Proposal) -> PositionCosts:
        """B2's model for the whole order: every leg is one order of lots x lot size units."""
        return PositionCosts(CycleTerms(lot=proposal.units, charges=self.charges, pad=self.pad))

    def max_loss(self, proposal: Proposal, market: Market) -> float:
        legs = [p.leg for p in proposal.legs]
        return self._costs(proposal).max_loss(legs, proposal.entry_prices(market))

    def entry_cash_flow(self, proposal: Proposal, market: Market) -> float:
        costs, legs, prices = self._costs(proposal), [p.leg for p in proposal.legs], proposal.entry_prices(market)
        fills = [max(costs.fill(leg, price, opening=True), 0.0) for leg, price in zip(legs, prices, strict=True)]
        premium = -sum(leg.side * fill for leg, fill in zip(legs, fills, strict=True))  # a fill is never below zero
        return premium * proposal.units - costs.charges(legs, prices, opening=True)
