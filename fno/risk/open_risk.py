"""Each position's maximum loss and bucket, the numbers C5's caps add up (design 6.1a, kind 1: the terminal-payoff loss
plus charges, fixed at entry).

A proposal's maximum loss is B2's model, the same number `MaxLossPerTrade` checks. An open trade's is the same model
applied to what the ledger holds: the cash it has moved so far (padded fills and entry charges, E1) plus its worst
value at expiry, plus each leg's exit pad and exit charges at that level (where several levels give the worst value,
the one with the larger exit charges, as B2). For a trade just entered at the modelled fills the two agree (tested).
Its extremes lie at strikes only when neither tail is net short; a held position with more calls or more puts sold than
bought is not defined risk and is refused, never measured. A position that can no longer lose counts as zero, never as
room for another trade.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from ..constants import OPTION_CALL, OPTION_PUT
from ..research_engine.cycle_costs import PAD, CycleTerms, PositionCosts
from ..research_engine.structures import BOUGHT, SOLD, Leg
from .buckets import Bucket, BucketMap
from .inputs import Market, OpenTrade, Proposal, RiskBook, RiskInputError
from .trade_costs import TradeCosts


@dataclass(frozen=True)
class PositionRisk:
    trade_id: str
    bucket: Bucket
    max_loss_rs: float
    opened_on: date | None
    proposed: bool = False


class HeldMaxLoss:
    """B2's maximum loss of a held position, from its signed units and its cash flow so far."""

    def __init__(self, charges: Mapping[str, float], pad: float = PAD):
        self.charges, self.pad = dict(charges), pad

    def _legs(self, units: Mapping[str, int], market: Market) -> list[tuple[Leg, int]]:
        legs = []
        for contract, count in units.items():
            quote = market.quote(contract)
            legs.append((Leg(quote.strike, quote.kind, BOUGHT if count > 0 else SOLD), abs(count)))
        for kind in (OPTION_CALL, OPTION_PUT):
            if sum(leg.side * n for leg, n in legs if leg.kind == kind) < 0:
                raise RiskInputError(f"more {kind} units sold than bought: the maximum loss is not fixed")
        return legs

    def _exit_charges(self, legs: list[tuple[Leg, int]], level: float) -> float:
        return sum(
            PositionCosts(CycleTerms(lot=n, charges=self.charges, pad=self.pad)).leg_charges(
                leg, leg.intrinsic(level), False
            )
            for leg, n in legs
        )

    def max_loss(self, units: Mapping[str, int], cash_flow: float, market: Market) -> float:
        legs = self._legs({c: n for c, n in units.items() if n}, market)
        if not legs:
            return 0.0
        worst = max(
            (round(-sum(leg.side * n * leg.intrinsic(level) for leg, n in legs), 6), self._exit_charges(legs, level))
            for level in {leg.strike for leg, _ in legs}
        )
        exit_pads = self.pad * sum(n for _, n in legs)
        return max(worst[0] - cash_flow + exit_pads + worst[1], 0.0)


class PositionRisks:
    """Every open trade's bucket and maximum loss, and the proposal's, for one book on one day."""

    def __init__(self, buckets: BucketMap, held: HeldMaxLoss, costs: TradeCosts):
        self.buckets, self.held, self.costs = buckets, held, costs

    def of_open(self, trade: OpenTrade, market: Market) -> PositionRisk:
        bucket = self.buckets.bucket_of(trade.terms.structure, trade.units)
        loss = self.held.max_loss(trade.units, trade.cash_flow, market)
        return PositionRisk(trade.trade_id, bucket, loss, trade.opened_on)

    def of_proposal(self, proposal: Proposal, market: Market) -> PositionRisk:
        bucket = self.buckets.bucket_of(proposal.terms.structure, proposal.signed_units())
        return PositionRisk(proposal.trade_id, bucket, self.costs.max_loss(proposal, market), market.day, True)

    def all(self, proposal: Proposal, book: RiskBook, market: Market) -> list[PositionRisk]:
        return [*(self.of_open(t, market) for t in book.open_trades), self.of_proposal(proposal, market)]
