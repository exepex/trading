"""The common opportunity set of a day (story E2, scoreboard A): every (approved version, expiry) eligible under its
playbook version, by D2's own opportunity code (DRY), plus the "no trade" opportunity. "Approved" is the registry's
status as of the start of the day (its latest row dated before the day), so a rebuild after a later approval or pause
gives the same set; a change takes effect from the next session."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date

from ..playbook.opportunities import BOOK, OpportunityFinder
from ..playbook.registry import RegistryRow
from ..playbook.schema import Strategy
from ..playbook.transitions import PAPER

NO_TRADE_OPPORTUNITY = {"opportunity_id": "no_trade"}


def approved_on(strategies: Sequence[Strategy], rows: Sequence[RegistryRow], day: date) -> list[Strategy]:
    status: dict[tuple[str, int], str] = {}
    for row in rows:
        if row.changed_on < day:
            status[row.key] = row.status
    return [s for s in strategies if status.get(s.key) == PAPER]


class OpportunitySet:
    def __init__(self, finder: OpportunityFinder):
        self.finder = finder

    def build(
        self, strategies: Sequence[Strategy], rows: Sequence[RegistryRow], day: date, monthly: Iterable[date]
    ) -> list[dict]:
        monthly = tuple(monthly)
        found = [o for s in approved_on(strategies, rows, day) for o in self.finder.find(s, day, monthly, BOOK)]
        entries = [
            {
                "opportunity_id": o.opportunity_id,
                "strategy": o.strategy.name,
                "version": o.strategy.version,
                "rule_sha256": o.strategy.parameters_sha256,
                "expiry": o.context.expiry.isoformat(),
                "entry_day": o.context.entry_day.isoformat(),
                "exit_day": o.context.exit_day.isoformat(),
            }  # fmt: skip
            for o in found
        ]
        return sorted(entries, key=lambda e: e["opportunity_id"]) + [NO_TRADE_OPPORTUNITY]
