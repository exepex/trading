"""Rules that compare today with the previous sessions: yesterday's high and low, and normal volume."""

from __future__ import annotations

from datetime import date

from ..indicators import MARKET_OPEN, clamp
from ..models import Candle, SignalVote
from .base import SignalRule, SymbolInputs


def last_session(history: list[Candle]) -> list[Candle]:
    if not history:
        return []
    day = history[-1].start.date()
    return [c for c in history if c.start.date() == day]


def volume_by_session(history: list[Candle], cutoff_minutes: int) -> dict[date, float]:
    """Volume traded in the first `cutoff_minutes` of each earlier session."""
    totals: dict[date, float] = {}
    for candle in history:
        start = candle.start
        minutes = (start.hour * 60 + start.minute) - (MARKET_OPEN.hour * 60 + MARKET_OPEN.minute)
        if minutes < cutoff_minutes:
            totals[start.date()] = totals.get(start.date(), 0.0) + candle.volume
    return totals


class PreviousDayLevels(SignalRule):
    """Trading above yesterday's high is a breakout; below yesterday's low a breakdown."""

    name = "previous_day_levels"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        yesterday = last_session(inputs.history)
        if not yesterday or not inputs.candles:
            return None
        high, low = max(c.high for c in yesterday), min(c.low for c in yesterday)
        price = inputs.closes[-1]
        if price > high:
            return self.vote(1.0, f"above yesterday's high {high:,.1f}")
        if price < low:
            return self.vote(-1.0, f"below yesterday's low {low:,.1f}")
        position = (price - low) / (high - low) if high > low else 0.5
        return self.vote(clamp(position * 2 - 1) * 0.3, f"inside yesterday's range {low:,.1f}-{high:,.1f}")


class VolumeConfirmation(SignalRule):
    """Heavy volume confirms today's move; light volume says nothing. Votes with the day's direction."""

    name = "volume_confirmation"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        if not inputs.candles or inputs.day_change_pct is None:
            return None
        start = inputs.candles[0].start
        elapsed = (inputs.candles[-1].start - start).seconds // 60 + 5
        earlier = volume_by_session(inputs.history, elapsed)
        normal = sum(earlier.values()) / len(earlier) if earlier else 0
        if normal <= 0:
            return None
        ratio = sum(c.volume for c in inputs.candles) / normal
        if ratio < self.settings.get("min_ratio", 1.3):
            return None
        strength = clamp((ratio - 1) / (self.settings.get("full_ratio", 2.5) - 1), 0.0, 1.0)
        direction = 1 if inputs.day_change_pct > 0 else -1
        return self.vote(direction * strength, f"volume {ratio:.1f}x normal for this time of day, backing the move")
