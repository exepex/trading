"""Votes from the market-brief research: recent verified news and the calibrated signal model."""

from __future__ import annotations

from ..indicators import clamp
from ..models import SignalVote
from .base import SignalRule, SymbolInputs


class NewsSentiment(SignalRule):
    """Average sentiment of the last day's material news; unverified stories count for half."""

    name = "news"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        news = inputs.research.news.get(inputs.symbol)
        if news is None:
            return None
        trust = 1.0 if news.trusted_items else self.settings.get("unverified_factor", 0.5)
        score = clamp(news.mean_sentiment / self.settings.get("full_scale", 0.4)) * trust
        label = "verified" if news.trusted_items else "unverified"
        return self.vote(score, f"{news.items} material {label} news item(s), latest: {news.latest_title[:80]}")


class ModelScore(SignalRule):
    """The market-brief model's calibrated probability that the stock rises over the next session."""

    name = "model"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        prob = inputs.research.model_prob_up.get(inputs.symbol)
        if prob is None:
            return None
        score = clamp((prob - 0.5) / self.settings.get("full_scale", 0.1))
        return self.vote(score, f"research model: {prob * 100:.0f}% chance of a rise next session")
