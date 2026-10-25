"""A fired opportunity's trade built on the day's live quotes (story D2): the structure code fixes the body strikes,
each width of the version is tried widest first, and the widest whose maximum loss (every charge and pad, C2's cost
model) is within the per-trade cap is kept. A width whose prices put the position at or beyond its payoff bounds (a
trade that cannot lose or cannot win) is skipped like an unlisted one, exactly as the research did (experiment 1
protocol "Impossible prices", `simulator._entry_trial`; judge 69), so the desk trades what was tested. The score is the
version's frozen expected net per opportunity divided by that maximum loss. Prices come only from valid quotes in the
market given; nothing is invented."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from ..research_engine.structures import Structure, payoff_bounds, position_value
from ..risk.inputs import Market, Proposal, ProposedLeg, RiskInputError, TradeTerms
from ..risk.trade_costs import TradeCosts
from .opportunities import Opportunity


@dataclass(frozen=True)
class Candidate:
    opportunity: Opportunity
    proposal: Proposal
    max_loss: float
    expected_net: float | None  # None: a research version without an honest estimate (shadow only)

    @property
    def score(self) -> float | None:
        """Expected net per rupee of maximum loss (D2's ranking); None without an estimate."""
        return None if self.expected_net is None else self.expected_net / self.max_loss

    def rank_key(self) -> tuple:
        """Higher score first (no estimate last); ties: lower maximum loss, earlier expiry, then name and version."""
        strategy, score = self.opportunity.strategy, self.score
        return (
            score is None,
            -(score or 0.0),
            self.max_loss,
            self.opportunity.context.expiry,
            strategy.name,
            strategy.version,
        )


class NotBuilt(ValueError):
    """The opportunity has no tradable structure today; the reason says why (no trade)."""


def live_chain(market: Market, expiry: date) -> dict[tuple[float, str], str]:
    """(strike, type) -> contract symbol for the expiry's contracts with a valid (not stale) quote."""
    return {(q.strike, q.kind): c for c, q in sorted(market.quotes.items()) if q.expiry == expiry and not q.stale}


class CandidateBuilder:
    def __init__(self, structures: Mapping[str, Structure], costs: TradeCosts, max_loss_cap: float, lot_size: int):
        self.structures, self.costs, self.cap, self.lot_size = dict(structures), costs, max_loss_cap, lot_size

    def build(self, opportunity: Opportunity, market: Market, trade_id: str) -> Candidate:
        """The widest width of the version whose trade is tradable today, at the version's lots."""
        spec, tried = opportunity.strategy.structure, []
        for width in spec.widths:
            built = self.at_terms(opportunity, market, trade_id, width, spec.lots)
            if isinstance(built, Candidate):
                return built
            tried.append(f"{width:g}: {built}")
        raise NotBuilt("no width tradable: " + "; ".join(tried))

    def at_terms(self, opportunity: Opportunity, market: Market, trade_id: str, width: float,
                 lots: int) -> Candidate | str:  # fmt: skip
        """The trade at one width and lot count, or why it is not tradable (story F5: Book 2's chosen width or fewer
        lots are rebuilt by the same code, never by hand)."""
        spec = opportunity.strategy.structure
        contracts = live_chain(market, opportunity.context.expiry)
        legs = self.structures[spec.code].legs(frozenset(contracts), market.spot, width)
        if legs is None:
            return "not listed with valid quotes"
        proposed = tuple(ProposedLeg(contracts[leg.contract], leg) for leg in legs)
        proposal = Proposal(trade_id, TradeTerms(spec.code, width, lots), self.lot_size, proposed)
        try:
            prices = proposal.entry_prices(market)
            max_loss = self.costs.max_loss(proposal, market)
        except RiskInputError as problem:
            return str(problem)
        lowest, highest = payoff_bounds(legs)
        if not lowest < position_value(legs, prices) < highest:
            return "bad prices (the position cannot lose or cannot win at expiry)"
        if max_loss > self.cap:
            return f"maximum loss {max_loss:.2f} above the cap {self.cap:g}"
        return Candidate(
            opportunity, proposal, max_loss, opportunity.strategy.evaluation_plan["expected_net_per_opportunity"]
        )
