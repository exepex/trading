"""Optional: the same research read from the stock tool's MotherDuck copy (a temporary trial database)."""

from __future__ import annotations

import logging
import os
from datetime import date, datetime

from ...constants import ENV_MOTHERDUCK_TOKEN
from .research_source import NewsItem, RegimeReading, ResearchSource

log = logging.getLogger(__name__)

RESEARCH_DATABASE = "market_brief"
MOTHERDUCK_URI = "md:{database}?motherduck_token={token}"
SCHEMA = "market_brief.{market}"
EARNINGS_EVENT_TYPE = "earnings"

REGIME_SQL = "select regime, stress, major_event_names from {schema}.regime order by computed_at desc limit 1"
EARNINGS_SQL = """
select ticker, min(date) as next_date from {schema}.events
where type = ? and date >= ? and ticker is not null group by ticker
"""
NEWS_SQL = """
select ticker, title, published_at, sentiment, materiality, status from {schema}.news
where ticker is not null and published_at >= ? order by published_at desc
"""
MODEL_SQL = """
select ticker, prob_up from {schema}.model_scores_latest where horizon_days = ?
qualify row_number() over (partition by ticker order by as_of_date desc) = 1
"""


class MotherDuckResearchSource(ResearchSource):
    def __init__(self, market: str = "india", token_env: str = ENV_MOTHERDUCK_TOKEN):
        self.schema = SCHEMA.format(market=market)
        self.token = os.environ.get(token_env)
        self._connection = None

    @property
    def available(self) -> bool:
        return bool(self.token)

    def _rows(self, sql: str, params: list | None = None) -> list[dict]:
        if not self.available:
            return []
        try:
            if self._connection is None:
                import duckdb

                self._connection = duckdb.connect(MOTHERDUCK_URI.format(database=RESEARCH_DATABASE, token=self.token))
            cursor = self._connection.execute(sql.format(schema=self.schema), params or [])
            names = [d[0] for d in cursor.description]
            return [dict(zip(names, row)) for row in cursor.fetchall()]
        except Exception as exc:  # research is optional input: never stop the desk for it
            log.warning("research query failed: %s", exc)
            self._connection = None
            return []

    def regime(self) -> RegimeReading | None:
        rows = self._rows(REGIME_SQL)
        if not rows:
            return None
        return RegimeReading(rows[0]["regime"], bool(rows[0]["stress"]), list(rows[0]["major_event_names"] or []))

    def upcoming_earnings(self, from_day: date) -> dict[str, date]:
        return {r["ticker"]: r["next_date"] for r in self._rows(EARNINGS_SQL, [EARNINGS_EVENT_TYPE, from_day])}

    def news_since(self, since: datetime) -> list[NewsItem]:
        return [
            NewsItem(r["ticker"], r["title"], r["published_at"], r["sentiment"], r["materiality"], r["status"])
            for r in self._rows(NEWS_SQL, [since])
        ]

    def model_prob_up(self, horizon_days: int) -> dict[str, float]:
        return {r["ticker"]: float(r["prob_up"]) for r in self._rows(MODEL_SQL, [horizon_days])}
