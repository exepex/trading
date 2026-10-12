"""Fast news as a signal and as a guard (stories from fno/live/news, scored by NewsRoom)."""

from __future__ import annotations

from ..models import GuardVerdict, SignalVote
from .base import GuardRule, SignalRule, SymbolInputs

MIN_PUSH = 0.05  # weaker news is noise: abstain
QUIET_REASON = "big news {age:.0f} min ago, direction unclear; waiting for the market to digest it: {title}"


class FastNews(SignalRule):
    """Weighted push of the last two hours' news: type, credibility, relevance and freshness."""

    name = "fast_news"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        pulse = inputs.news
        if pulse is None or abs(pulse.score) < MIN_PUSH or pulse.strongest is None:
            return None
        return self.vote(pulse.score, pulse.strongest.reason)


class NewsShockGuard(GuardRule):
    """No new trade in the minutes after credible, high-impact news whose direction is not yet clear."""

    name = "news_shock"

    def evaluate(self, inputs: SymbolInputs) -> GuardVerdict:
        pulse = inputs.news
        if pulse is None:
            return self.verdict(False, "no fast news")
        unclear = pulse.major_unclear(self.settings.get("quiet_minutes", 15), self.settings.get("min_weight", 0.45))
        if unclear is None:
            return self.verdict(False, "no unclear major news")
        return self.verdict(True, QUIET_REASON.format(age=unclear.age_minutes, title=unclear.story.title[:80]))
