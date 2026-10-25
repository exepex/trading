"""Book 2's D2 evaluation (story F5): D2's own `RuleEvaluator` over Book 2's tradable versions (`Book2Playbook`, read
from the run's snapshot) on Book 2's own account. With no picks it gives the rule default (the day sheet); with the
AI's picks, through F6's shared `SelectionAllocator`, it gives the decision; rebuilt from a run's stored picks it is
the replay behind orders. The no-trade threshold binds Book 2's `paper` versions only: a research version is allocated
as D2's shadow test allocates it (owner's Q11 and Q12 (A), assumption pending the owner's word), so a research rule
Book 2 may trade is never refused for its missing or negative estimate. A changed width or fewer lots is rebuilt by
D2's `CandidateBuilder.at_terms`, never by hand."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ..constants import BOOK2_HYBRID
from ..playbook.allocation import Allocator, Placed, StrategyTradeCounts
from ..playbook.candidates import Candidate, CandidateBuilder, NotBuilt
from ..playbook.evaluate import RuleEvaluator
from ..playbook.opportunities import OpportunityFinder
from ..playbook.selection import NOT_CHOSEN, Pick, SelectionAllocator
from ..playbook.shadow import RealBooks
from ..playbook.transitions import PAPER
from ..risk.inputs import Market, RiskBook


def binds_paper(candidate: Candidate) -> bool:
    """Whether the no-trade threshold binds this candidate: only a `paper` version's."""
    return candidate.opportunity.strategy.status == PAPER


class RuleDefaultAllocator:
    """D2's allocator for Book 2's rule default: the threshold as `binds_paper` says, whatever the caller passes."""

    def __init__(self, inner: Allocator):
        self.inner = inner

    def allocate(self, candidates: Sequence[Candidate], book: RiskBook, market: Market, counts: StrategyTradeCounts,
                 threshold: bool = True) -> list[Placed]:  # fmt: skip
        return self.inner.allocate(candidates, book, market, counts, binds_paper)


class Book2Evaluators:
    def __init__(self, finder: OpportunityFinder, builder: CandidateBuilder, allocator: Allocator, real: RealBooks):
        self.finder, self.builder, self.allocator, self.real = finder, builder, allocator, real

    def rule_default(self) -> RuleEvaluator:
        return RuleEvaluator(self.finder, self.builder, RuleDefaultAllocator(self.allocator), self.real)

    def with_picks(self, picks: Sequence[Pick], market: Market,
                   unpicked: str = NOT_CHOSEN) -> tuple[RuleEvaluator, SelectionAllocator]:  # fmt: skip
        selection = SelectionAllocator(self.allocator, picks, BOOK2_HYBRID, binds_paper, self._rebuild(market),
                                       unpicked)  # fmt: skip
        return RuleEvaluator(self.finder, self.builder, selection, self.real), selection

    def from_stored(self, stored: Sequence[Mapping], market: Market) -> RuleEvaluator:
        """The evaluator a committed run was decided with, from the picks in its `inputs.json`."""
        return self.with_picks([Pick.from_json(p) for p in stored], market)[0]

    def _rebuild(self, market: Market):
        def rebuild(candidate: Candidate, pick: Pick) -> Candidate:
            terms = candidate.proposal.terms
            width = terms.width if pick.width is None else float(pick.width)
            lots = terms.lots if pick.lots is None else int(pick.lots)
            built = self.builder.at_terms(candidate.opportunity, market, candidate.proposal.trade_id, width, lots)
            if isinstance(built, str):
                raise NotBuilt(f"{width:g} x {lots}: {built}")
            return built

        return rebuild
