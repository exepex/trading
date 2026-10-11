"""Hard filters: F&O ban list, earnings too close, market-wide stress."""

from __future__ import annotations

from ..models import GuardVerdict
from .base import GuardRule, SymbolInputs


class BanListGuard(GuardRule):
    name = "ban_list"

    def evaluate(self, inputs: SymbolInputs) -> GuardVerdict:
        banned = inputs.symbol in inputs.banned
        return self.verdict(banned, f"{inputs.symbol} is in today's F&O ban list" if banned else "not banned")


class EarningsGuard(GuardRule):
    """Option prices collapse after results (IV crush), so do not buy options just before them."""

    name = "earnings"

    def evaluate(self, inputs: SymbolInputs) -> GuardVerdict:
        days = inputs.research.days_to_earnings(inputs.symbol, inputs.now.date()) if inputs.now else None
        limit = self.settings.get("min_days_before_results", 2)
        blocked = days is not None and days < limit
        reason = f"results in {days} day(s)" if days is not None else "no results date in research"
        return self.verdict(blocked, reason)


class MarketStressGuard(GuardRule):
    """The market-brief regime flags market-wide stress: no new trades anywhere."""

    name = "market_stress"

    def evaluate(self, inputs: SymbolInputs) -> GuardVerdict:
        research = inputs.research
        blocked = research.stress and self.settings.get("block_on_stress", True)
        return self.verdict(blocked, f"market regime {research.regime or 'unknown'}, stress {research.stress}")
