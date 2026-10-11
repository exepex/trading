"""Intraday price-action rules: opening range, VWAP, short-term trend, strength versus the index."""

from __future__ import annotations

from ..indicators import clamp, ema_gap_pct, opening_range, vwap
from ..models import SignalVote
from .base import SignalRule, SymbolInputs


class OpeningRangeBreakout(SignalRule):
    """Above the first-15-minute high is bullish, below the low bearish."""

    name = "opening_range"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        window = opening_range(inputs.candles, self.settings.get("minutes", 15))
        if window is None:
            return None
        high, low = window
        price = inputs.closes[-1]
        if price > high:
            return self.vote(1.0, f"broke above the opening-range high {high:,.1f}")
        if price < low:
            return self.vote(-1.0, f"broke below the opening-range low {low:,.1f}")
        return self.vote(0.0, f"inside the opening range {low:,.1f}-{high:,.1f}")


class VwapPosition(SignalRule):
    """Trading above VWAP means buyers are in control today."""

    name = "vwap"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        level = vwap(inputs.candles)
        if level is None:
            return None
        gap_pct = (inputs.closes[-1] / level - 1) * 100
        full_scale = self.settings.get("full_scale_pct", 0.6)
        side = "above" if gap_pct >= 0 else "below"
        return self.vote(clamp(gap_pct / full_scale), f"{abs(gap_pct):.2f}% {side} VWAP {level:,.1f}")


class IntradayTrend(SignalRule):
    """Fast versus slow EMA on 5-minute closes."""

    name = "intraday_trend"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        fast, slow = self.settings.get("fast", 9), self.settings.get("slow", 21)
        gap = ema_gap_pct(inputs.closes, fast, slow)
        if gap is None:
            return None
        full_scale = self.settings.get("full_scale_pct", 0.3)
        word = "up" if gap >= 0 else "down"
        return self.vote(clamp(gap / full_scale), f"5-min trend {word} (EMA{fast} vs EMA{slow} gap {gap:+.2f}%)")


class RelativeStrength(SignalRule):
    """Outperforming NIFTY today is bullish for the stock, underperforming bearish."""

    name = "relative_strength"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        own = inputs.snapshot.day_change_pct
        if own is None or inputs.benchmark_change_pct is None:
            return None
        diff = own - inputs.benchmark_change_pct
        full_scale = self.settings.get("full_scale_pct", 1.5)
        word = "stronger" if diff >= 0 else "weaker"
        return self.vote(clamp(diff / full_scale), f"{abs(diff):.2f}% {word} than NIFTY today ({own:+.2f}%)")
