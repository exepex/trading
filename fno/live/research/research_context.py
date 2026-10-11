"""Research the market-brief tool already produced for India: regime, earnings dates, verified news, model scores."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from ...constants import TRUSTED_NEWS_STATUSES, UNTRUSTED_NEWS_STATUSES
from .warehouse import ResearchWarehouse

MARKET_SCHEMA = "market_brief.india"
MATERIAL_LEVELS = ("medium", "high")
EARNINGS_EVENT_TYPE = "earnings"
MODEL_HORIZON_DAYS = 1

REGIME_SQL = f"""
select regime, stress, major_event_names, session_date
from {MARKET_SCHEMA}.regime order by computed_at desc limit 1
"""
EARNINGS_SQL = f"""
select ticker, min(date) as next_date
from {MARKET_SCHEMA}.events
where type = ? and date >= ? and ticker is not null
group by ticker
"""
NEWS_SQL = f"""
select ticker, sentiment, materiality, status, title, published_at
from {MARKET_SCHEMA}.news
where ticker is not null and published_at >= ? and materiality in ({", ".join("?" for _ in MATERIAL_LEVELS)})
order by published_at desc
"""
MODEL_SQL = f"""
select ticker, prob_up from {MARKET_SCHEMA}.model_scores_latest
where horizon_days = ?
qualify row_number() over (partition by ticker order by as_of_date desc) = 1
"""


@dataclass
class NewsSignal:
    """Recent material news on one company, summarised."""

    mean_sentiment: float  # -1..+1, as scored by the market-brief news analyst
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

    def days_to_earnings(self, symbol: str, today: date) -> int | None:
        when = self.next_earnings.get(symbol)
        return (when - today).days if when else None


class ResearchContextLoader:
    def __init__(self, warehouse: ResearchWarehouse, news_lookback_hours: int = 24):
        self.warehouse = warehouse
        self.news_lookback = timedelta(hours=news_lookback_hours)

    def load(self, now: datetime, news_since: datetime | None = None) -> ResearchSnapshot:
        """news_since: usually the previous session's close; defaults to the fixed lookback."""
        snapshot = ResearchSnapshot(loaded_at=now)
        if not self.warehouse.available:
            return snapshot
        self._load_regime(snapshot)
        snapshot.next_earnings = {
            r["ticker"]: r["next_date"] for r in self.warehouse.rows(EARNINGS_SQL, [EARNINGS_EVENT_TYPE, now.date()])
        }
        since = min(news_since, now - self.news_lookback) if news_since else now - self.news_lookback
        snapshot.news = summarise_news(self.warehouse.rows(NEWS_SQL, [since, *MATERIAL_LEVELS]))
        snapshot.model_prob_up = {
            r["ticker"]: float(r["prob_up"]) for r in self.warehouse.rows(MODEL_SQL, [MODEL_HORIZON_DAYS])
        }
        return snapshot

    def _load_regime(self, snapshot: ResearchSnapshot) -> None:
        rows = self.warehouse.rows(REGIME_SQL)
        if rows:
            snapshot.regime = rows[0]["regime"]
            snapshot.stress = bool(rows[0]["stress"])
            snapshot.major_events = list(rows[0]["major_event_names"] or [])


def summarise_news(rows: list[dict]) -> dict[str, NewsSignal]:
    """Average sentiment per company, ignoring rumours, promotions and contradicted stories."""
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        if row.get("status") in UNTRUSTED_NEWS_STATUSES or row.get("sentiment") is None:
            continue
        grouped.setdefault(row["ticker"], []).append(row)
    out = {}
    for ticker, items in grouped.items():
        out[ticker] = NewsSignal(
            mean_sentiment=sum(float(i["sentiment"]) for i in items) / len(items),
            items=len(items),
            trusted_items=sum(i.get("status") in TRUSTED_NEWS_STATUSES for i in items),
            latest_title=items[0]["title"],
        )
    return out
