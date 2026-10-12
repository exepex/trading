"""Hard filters: F&O ban list, earnings too close, market-wide stress."""

from __future__ import annotations

import math

from ...analytics import atm_iv
from ..models import Candle, GuardVerdict
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
    """Market-wide risk from the stock tool's research: a stressed regime or high-impact geopolitical news."""

    name = "market_stress"

    def evaluate(self, inputs: SymbolInputs) -> GuardVerdict:
        research = inputs.research
        if research.stress and self.settings.get("block_on_stress", True):
            return self.verdict(True, f"market regime {research.regime or 'unknown'} under stress")
        if research.major_events and self.settings.get("block_on_major_event", True):
            return self.verdict(True, f"major scheduled event: {', '.join(research.major_events)[:80]}")
        if research.geopolitical_headlines and self.settings.get("block_on_geopolitical", True):
            return self.verdict(True, f"high-impact geopolitical news: {research.geopolitical_headlines[0][:80]}")
        return self.verdict(False, f"market regime {research.regime or 'unknown'}, no stress")


INTRADAY_BARS_PER_YEAR = 75 * 252  # 5-minute bars in an NSE session x trading days


def realised_volatility(candles: list[Candle]) -> float | None:
    """Annualised volatility from 5-minute returns within each session (overnight gaps excluded), e.g. 0.14."""
    returns = [
        math.log(b.close / a.close)
        for a, b in zip(candles, candles[1:])
        if a.start.date() == b.start.date() and a.close > 0 and b.close > 0
    ]
    if len(returns) < 30:
        return None
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(variance * INTRADAY_BARS_PER_YEAR)


class ExpensiveOptionsGuard(GuardRule):
    """Do not buy options priced for far bigger moves than the stock actually makes: time decay wins."""

    name = "expensive_options"

    def evaluate(self, inputs: SymbolInputs) -> GuardVerdict:
        if inputs.chain is None:
            return self.verdict(False, "no option chain")
        implied = atm_iv(inputs.chain)
        realised = realised_volatility(inputs.history + inputs.candles)
        if implied is None or not realised:
            return self.verdict(False, "volatility not measurable")
        ratio = implied / realised
        limit = self.settings.get("max_iv_to_realised", 1.6)
        return self.verdict(
            ratio > limit,
            f"options priced at {implied * 100:.0f}% vol vs {realised * 100:.0f}% realised ({ratio:.1f}x)",
        )


class IvRankGuard(GuardRule):
    """No option purchase when options are dear against their own history (IV rank above the limit).
    Abstains until the desk has stored enough daily IV snapshots (see fno/live/learning/iv_history.py)."""

    name = "iv_rank"

    def evaluate(self, inputs: SymbolInputs) -> GuardVerdict:
        limit = self.settings.get("max_iv_rank", 80)
        if inputs.iv_rank is None:
            return self.verdict(False, "not enough IV history yet")
        if inputs.iv_rank > limit:
            return self.verdict(True, f"options dear: IV rank {inputs.iv_rank:.0f} above {limit}")
        return self.verdict(False, f"IV rank {inputs.iv_rank:.0f}")
