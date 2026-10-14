"""Story D2: the day's rule evaluation and allocation, Book 1's decision. For each approved (`paper`) version, every
opportunity today is evaluated on the live 15:00 feature values; a fired rule builds its trade on live quotes, and the
fixed allocation rule chooses among the valid candidates for the book's account. Each registered research candidate
is evaluated the same way against its own shadow book (owner, 14 Oct 2026: forward shadow test), never Book 1's. A
day with nothing approved allocates nothing; every opportunity, traded or not, gets an outcome."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import date

from ..constants import BOOKS, Decision
from ..research_engine.features import DecisionContext, FeatureValue
from ..risk.inputs import Market, RiskBook
from .allocation import Allocator, StrategyTradeCounts
from .candidates import CandidateBuilder, NotBuilt
from .conditions import unmet_conditions
from .loader import Playbook
from .opportunities import BOOK, SHADOW, Opportunity, OpportunityFinder
from .outcomes import DayEvaluation, Outcome
from .schema import Strategy

SHADOW_DECISIONS = {Decision.CHOSEN: Decision.SHADOW_TRADE}


class LiveFeatureValues(ABC):
    @abstractmethod
    def values(self, day: date, context: DecisionContext) -> Mapping[str, FeatureValue]:
        """Every live 15:00 feature (B7) for this decision context, by live feature name; None when unknown."""


class ShadowBooks(ABC):
    @abstractmethod
    def book(self, strategy: Strategy) -> tuple[RiskBook, StrategyTradeCounts]:
        """The research candidate's own shadow paper account and its trade counts (never Book 1's)."""


class RuleEvaluator:
    def __init__(self, finder: OpportunityFinder, builder: CandidateBuilder, allocator: Allocator):
        self.finder, self.builder, self.allocator = finder, builder, allocator

    def evaluate(
        self,
        day: date,
        playbook: Playbook,
        market: Market,
        features: LiveFeatureValues,
        book: RiskBook,
        counts: StrategyTradeCounts,
        shadow_books: ShadowBooks,
    ) -> DayEvaluation:
        monthly = tuple(market.futures)  # NIFTY futures list only the monthly expiries
        found = [o for s in playbook.approved() for o in self.finder.find(s, day, monthly, BOOK)]
        outcomes = self._allocate(day, found, market, features, book, counts)
        for strategy in playbook.shadow():  # each research candidate alone, in its own shadow book
            shadow_book, shadow_counts = shadow_books.book(strategy)
            found = self.finder.find(strategy, day, monthly, SHADOW)
            if shadow_book.name in BOOKS or shadow_book.name == book.name:  # misconfigured: never a real account
                outcomes += [
                    _no_trade(o, {}, f"refused: shadow book {shadow_book.name!r} is a real book") for o in found
                ]
                continue
            outcomes += self._allocate(day, found, market, features, shadow_book, shadow_counts, threshold=False)
        return DayEvaluation(day.isoformat(), book.name, tuple(sorted(outcomes, key=_order)))

    def _allocate(self, day, found, market, features, book, counts, threshold: bool = True) -> list[Outcome]:
        outcomes, candidates, seen = [], [], {}
        for opportunity in found:
            seen[opportunity.opportunity_id] = values = dict(features.values(day, opportunity.context))
            unmet = tuple(unmet_conditions(opportunity.strategy, values))
            if unmet:
                outcomes.append(_no_trade(opportunity, values, "rule did not fire", unmet))
                continue
            try:
                candidates.append(self.builder.build(opportunity, market, _trade_id(day, opportunity)))
            except NotBuilt as reason:
                outcomes.append(_no_trade(opportunity, values, str(reason)))
        for candidate, decision, reason, risk in self.allocator.allocate(candidates, book, market, counts, threshold):
            opportunity = candidate.opportunity
            if opportunity.mode == SHADOW:
                decision = SHADOW_DECISIONS.get(decision, Decision.SHADOW_NO_TRADE)
            outcomes.append(
                Outcome(opportunity, seen[opportunity.opportunity_id], decision, reason, (), candidate, risk)
            )
        return outcomes


def _no_trade(opportunity: Opportunity, values, reason: str, unmet: tuple[str, ...] = ()) -> Outcome:
    decision = Decision.SHADOW_NO_TRADE if opportunity.mode == SHADOW else Decision.NO_TRADE
    return Outcome(opportunity, values, decision, reason, unmet)


def _trade_id(day: date, opportunity: Opportunity) -> str:
    prefix = "shadow-" if opportunity.mode == SHADOW else ""
    return f"{prefix}{day.isoformat()}-{opportunity.opportunity_id}"


def _order(outcome: Outcome) -> tuple:
    return outcome.opportunity.mode != BOOK, outcome.opportunity.opportunity_id
