"""The research snapshot the signal rules read: regime, earnings dates, scored news, model scores, geopolitical risk."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from ...constants import TRUSTED_NEWS_STATUSES, UNTRUSTED_NEWS_STATUSES
from .research_source import Announcement, NewsItem, ResearchSource

MATERIAL_LEVELS = ("medium", "high")
HIGH_MATERIALITY = "high"
MODEL_HORIZON_DAYS = 1
DEALS_LOOKBACK_DAYS = 5
FLOWS_LOOKBACK_DAYS = 7


@dataclass
class NewsSignal:
    """Recent material news on one company, summarised."""

    mean_sentiment: float  # -1..+1, as scored by the stock tool's news analyst
    items: int
    trusted_items: int  # confirmed by a primary source or corroborated
    latest_title: str


@dataclass
class ResearchSnapshot:
    loaded_at: datetime | None = None
    regime: str | None = None
    stress: bool = False
    major_events: list[str] = field(default_factory=list)
    next_earnings: dict[str, date] = field(default_factory=dict)
    news: dict[str, NewsSignal] = field(default_factory=dict)
    model_prob_up: dict[str, float] = field(default_factory=dict)
    geopolitical_headlines: list[str] = field(default_factory=list)  # high-materiality geopolitical stories
    announcements: dict[str, list[Announcement]] = field(default_factory=dict)  # filings since the last close
    block_deal_net: dict[str, float] = field(default_factory=dict)  # rupees, recent block/bulk deals
    foreign_flows_cr: list[float] = field(default_factory=list)  # daily net FPI equity buying, oldest first

    def days_to_earnings(self, symbol: str, today: date) -> int | None:
        when = self.next_earnings.get(symbol)
        return (when - today).days if when else None


class ResearchContextLoader:
    def __init__(self, source: ResearchSource, news_lookback_hours: int = 24):
        self.source = source
        self.news_lookback = timedelta(hours=news_lookback_hours)

    def load(self, now: datetime, news_since: datetime | None = None) -> ResearchSnapshot:
        """news_since: usually the previous session's close; the fixed lookback applies if it is earlier."""
        snapshot = ResearchSnapshot(loaded_at=now)
        self.source.refresh()  # first, so a first run downloads the research before checking for it
        if not self.source.available:
            return snapshot
        regime = self.source.regime()
        if regime:
            snapshot.regime, snapshot.stress, snapshot.major_events = regime.regime, regime.stress, regime.major_events
        snapshot.next_earnings = self.source.upcoming_earnings(now.date())
        since = min(news_since, now - self.news_lookback) if news_since else now - self.news_lookback
        news = self.source.news_since(since)
        snapshot.news = summarise_news(news)
        snapshot.geopolitical_headlines = geopolitical_headlines(news)
        snapshot.model_prob_up = self.source.model_prob_up(MODEL_HORIZON_DAYS)
        for filing in self.source.announcements_since(since):
            snapshot.announcements.setdefault(filing.ticker, []).append(filing)
        snapshot.block_deal_net = self.source.block_deal_net_value(now.date() - timedelta(days=DEALS_LOOKBACK_DAYS))
        flows = self.source.foreign_flows(now.date() - timedelta(days=FLOWS_LOOKBACK_DAYS))
        snapshot.foreign_flows_cr = [net for _, net in flows]
        return snapshot


def is_usable(item: NewsItem) -> bool:
    """Scored, material, and not a rumour, promotion or contradicted story."""
    return (
        item.sentiment is not None
        and item.materiality in MATERIAL_LEVELS
        and item.status not in UNTRUSTED_NEWS_STATUSES
    )


def summarise_news(items: list[NewsItem]) -> dict[str, NewsSignal]:
    """Average sentiment per company from usable stories; items arrive newest first."""
    grouped: dict[str, list[NewsItem]] = {}
    for item in items:
        if is_usable(item):
            grouped.setdefault(item.ticker, []).append(item)
    return {
        ticker: NewsSignal(
            mean_sentiment=sum(float(i.sentiment) for i in stories) / len(stories),
            items=len(stories),
            trusted_items=sum(i.status in TRUSTED_NEWS_STATUSES for i in stories),
            latest_title=stories[0].title,
        )
        for ticker, stories in grouped.items()
    }


def geopolitical_headlines(items: list[NewsItem]) -> list[str]:
    seen, headlines = set(), []
    for item in items:
        if item.geopolitical and item.materiality == HIGH_MATERIALITY and item.title not in seen:
            seen.add(item.title)
            headlines.append(item.title)
    return headlines
