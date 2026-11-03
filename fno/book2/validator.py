"""Book 2's C4 validator in its decision run (story F5): C4's own adapter, adding to each chosen trade the two inputs
`EnvelopeMode` needs that D2's outcome does not carry. The rule default is the terms of the slot's default as D2's
rule-default evaluation built them, never the AI's (judge 260). The counts are the version's completed and open paper
trades as the run's counts read them (live in the decision, recorded in a replay), asked exactly as D2's allocator
asks them, so a replay reproduces every C4 result."""

from __future__ import annotations

from collections.abc import Mapping

from ..checks.validity_adapter import BookTradeValidator
from ..constants import UNPROVEN_BELOW_COMPLETED_TRADES
from ..playbook.allocation import StrategyTradeCounts
from ..playbook.envelope import BookTerms
from ..playbook.outcomes import Outcome


class Book2TradeValidator(BookTradeValidator):
    def __init__(self, base: BookTradeValidator, defaults: Mapping[str, BookTerms], counts: StrategyTradeCounts):
        """`defaults`: each chosen opportunity -> its slot's rule-default terms."""
        super().__init__(base.book, base.checker, base.captures, base.cutoff, base.log)
        self.defaults, self.counts = dict(defaults), counts

    def extra(self, outcome: Outcome) -> dict:
        name, version = outcome.opportunity.strategy.key
        completed = self.counts.completed(name, version)
        held = self.counts.open(name, version) if completed < UNPROVEN_BELOW_COMPLETED_TRADES else 0
        return {"rule_default": self.defaults.get(outcome.opportunity.opportunity_id),
                "version_counts": (completed, held)}  # fmt: skip
