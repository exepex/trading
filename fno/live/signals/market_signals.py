"""Market-wide rules: sector strength, breadth across F&O names, global markets, India VIX direction."""

from __future__ import annotations

from ..indicators import clamp
from ..models import SignalVote
from .base import SignalRule, SymbolInputs


class SectorStrength(SignalRule):
    """A stock in a sector beating NIFTY today has the wind behind it."""

    name = "sector_strength"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        sector = inputs.backdrop.sector_change_for(inputs.industry)
        if sector is None or inputs.benchmark_change_pct is None:
            return None
        lead = sector - inputs.benchmark_change_pct
        word = "leading" if lead >= 0 else "lagging"
        return self.vote(
            clamp(lead / self.settings.get("full_scale_pct", 1.0)),
            f"{inputs.industry} sector {sector:+.2f}% today, {word} NIFTY by {abs(lead):.2f}%",
        )


class MarketBreadth(SignalRule):
    """How many F&O stocks are up versus down: a broad rally or sell-off lifts or sinks most names."""

    name = "market_breadth"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        backdrop = inputs.backdrop
        if backdrop.breadth is None:
            return None
        score = clamp(backdrop.breadth / self.settings.get("full_scale", 0.6))
        return self.vote(score, f"breadth: {backdrop.advancers} F&O stocks up, {backdrop.decliners} down")


class GlobalCues(SignalRule):
    """US futures, Nikkei and Hang Seng: global risk appetite today."""

    name = "global_cues"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        move = inputs.backdrop.global_change_pct
        if move is None:
            return None
        score = clamp(move / self.settings.get("full_scale_pct", 1.0))
        return self.vote(score, f"global markets {move:+.2f}% on average (US futures, Nikkei, Hang Seng)")


class VixDirection(SignalRule):
    """Rising India VIX means rising fear: bearish for the market, and options get dearer."""

    name = "vix_direction"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        move = inputs.backdrop.vix_change_pct
        if move is None:
            return None
        word = "rising" if move > 0 else "falling"
        return self.vote(clamp(-move / self.settings.get("full_scale_pct", 8.0)), f"India VIX {word} {move:+.1f}%")
