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


class AnnouncementCatalyst(SignalRule):
    """A fresh exchange filing plus a decisive price move: the market is reacting, so follow the reaction.

    Filings carry no direction of their own; routine ones (newspaper copies, trading windows...) are ignored.
    """

    name = "announcement"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        ignored = {c.lower() for c in self.settings.get("ignored_categories", [])}
        filings = [f for f in inputs.research.announcements.get(inputs.symbol, []) if f.category.lower() not in ignored]
        move = inputs.day_change_pct
        if not filings or move is None or abs(move) < self.settings.get("min_move_pct", 1.0):
            return None
        score = clamp(move / self.settings.get("full_scale_pct", 3.0))
        return self.vote(score, f"price reacting {move:+.2f}% to a fresh filing: {filings[-1].category}")


class BlockDealFlow(SignalRule):
    """Net institutional buying or selling through block and bulk deals in the last few sessions."""

    name = "block_deals"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        net = inputs.research.block_deal_net.get(inputs.symbol)
        if not net:
            return None
        crore = net / 1e7
        word = "bought" if net > 0 else "sold"
        score = clamp(crore / self.settings.get("full_scale_crore", 200.0))
        return self.vote(score, f"block/bulk deals: net Rs {abs(crore):,.0f} crore {word} recently")


class ForeignFlow(SignalRule):
    """Foreign investors' net buying of Indian shares over the last sessions: a market-wide tide."""

    name = "foreign_flows"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        days = self.settings.get("days", 3)
        flows = inputs.research.foreign_flows_cr[-days:]
        if not flows:
            return None
        total = sum(flows)
        word = "bought" if total > 0 else "sold"
        score = clamp(total / self.settings.get("full_scale_crore", 10000.0))
        return self.vote(score, f"foreign investors net {word} Rs {abs(total):,.0f} crore over {len(flows)} session(s)")
