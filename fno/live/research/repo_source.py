"""Reads the stock tool's research from its date-partitioned JSONL files.

Layout: data/<market>/<dataset>/YYYY/MM/<date>.jsonl, append-only (a record may appear in several versions).
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from datetime import date, datetime, timedelta
from pathlib import Path

from .repo_sync import ResearchRepoSync
from .research_source import Announcement, NewsItem, RegimeReading, ResearchSource

log = logging.getLogger(__name__)

NEWS = "news"
NEWS_ENRICHED = "news_enriched"
NEWS_VERIFIED = "news_verified"
EVENTS = "events"
REGIME = "regime"
MODEL_SCORES = "model_scores"
ANNOUNCEMENTS = "announcements"
DEALS = "deals"
FPI = "fpi"
DATASETS = (NEWS, NEWS_ENRICHED, NEWS_VERIFIED, EVENTS, REGIME, MODEL_SCORES, ANNOUNCEMENTS, DEALS, FPI)
FPI_EQUITY, FPI_SECONDARY_MARKET = "Equity", "Stock Exchange"
DEAL_BUY = "buy"
EARNINGS_EVENT_TYPE = "earnings"
FILE_PATTERN = "*.jsonl"


def parse_time(text: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(text) if text else None
    except ValueError:
        return None


class RepoResearchSource(ResearchSource):
    def __init__(self, market_dir: Path, sync: ResearchRepoSync | None = None):
        self.market_dir = market_dir
        self.sync = sync

    @property
    def available(self) -> bool:
        return self.market_dir.is_dir()

    def refresh(self) -> None:
        if self.sync:
            self.sync.sync()

    # ------------------------------------------------------------------ file access

    def _files(self, dataset: str, since_day: date | None = None) -> list[Path]:
        files = sorted((self.market_dir / dataset).rglob(FILE_PATTERN))
        if since_day is None:
            return files
        return [f for f in files if f.stem >= since_day.isoformat()]

    def _rows(self, files: list[Path]) -> Iterator[dict]:
        for path in files:
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        log.warning("skipping a malformed line in %s", path)

    # ------------------------------------------------------------------ research

    def regime(self) -> RegimeReading | None:
        rows = list(self._rows(self._files(REGIME)[-2:]))
        if not rows:
            return None
        latest = max(rows, key=lambda r: r.get("computed_at") or "")
        return RegimeReading(
            latest.get("regime"), bool(latest.get("stress")), list(latest.get("major_event_names") or [])
        )

    def upcoming_earnings(self, from_day: date) -> dict[str, date]:
        upcoming: dict[str, date] = {}
        for row in self._rows(self._files(EVENTS)):
            if row.get("type") != EARNINGS_EVENT_TYPE or not row.get("ticker") or not row.get("date"):
                continue
            when = date.fromisoformat(row["date"])
            if when >= from_day and (row["ticker"] not in upcoming or when < upcoming[row["ticker"]]):
                upcoming[row["ticker"]] = when
        return upcoming

    def news_since(self, since: datetime) -> list[NewsItem]:
        first_file_day = since.date() - timedelta(days=1)  # a story can be filed on the day after it was published
        analysis = self._latest_by_id(self._rows(self._files(NEWS_ENRICHED, first_file_day)), "analyzed_at")
        statuses = self._verification_statuses(first_file_day)
        items = []
        for row in self._rows(self._files(NEWS, first_file_day)):
            published = parse_time(row.get("published_at"))
            if published is None or published < since:
                continue
            scored = analysis.get(row["id"], {})
            for ticker in row.get("tickers") or []:
                items.append(
                    NewsItem(
                        ticker=ticker,
                        title=row.get("title", ""),
                        published_at=published,
                        sentiment=scored.get("sentiment"),
                        materiality=scored.get("materiality"),
                        status=statuses.get(row["id"]),
                        geopolitical=bool(scored.get("geopolitical")),
                    )
                )
        return sorted(items, key=lambda i: i.published_at, reverse=True)

    def model_prob_up(self, horizon_days: int) -> dict[str, float]:
        latest: dict[str, tuple[str, float]] = {}
        for row in self._rows(self._files(MODEL_SCORES)[-3:]):
            if row.get("horizon_days") != horizon_days or row.get("prob_up") is None:
                continue
            as_of = row.get("as_of_date") or ""
            if row["ticker"] not in latest or as_of > latest[row["ticker"]][0]:
                latest[row["ticker"]] = (as_of, float(row["prob_up"]))
        return {ticker: prob for ticker, (_, prob) in latest.items()}

    def announcements_since(self, since: datetime) -> list[Announcement]:
        items = []
        for row in self._rows(self._files(ANNOUNCEMENTS, since.date() - timedelta(days=1))):
            published = parse_time(row.get("published_at"))
            if published and published >= since and row.get("ticker"):
                items.append(Announcement(row["ticker"], row.get("category", ""), row.get("subject", ""), published))
        return items

    def block_deal_net_value(self, since_day: date) -> dict[str, float]:
        net: dict[str, float] = {}
        seen: set[str] = set()
        for row in self._rows(self._files(DEALS, since_day)):
            if row["id"] in seen or not row.get("ticker") or row.get("date", "") < since_day.isoformat():
                continue
            seen.add(row["id"])
            sign = 1 if row.get("side") == DEAL_BUY else -1
            net[row["ticker"]] = net.get(row["ticker"], 0.0) + sign * float(row.get("value") or 0)
        return net

    def foreign_flows(self, since_day: date) -> list[tuple[date, float]]:
        by_day: dict[date, float] = {}
        for row in self._rows(self._files(FPI, since_day)):
            if row.get("asset_class") == FPI_EQUITY and row.get("route") == FPI_SECONDARY_MARKET:
                by_day[date.fromisoformat(row["reporting_date"])] = float(row.get("net_cr") or 0)
        return sorted(by_day.items())

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _latest_by_id(rows: Iterator[dict], time_field: str) -> dict[str, dict]:
        """Append-only files can hold several versions of a record: keep the newest."""
        latest: dict[str, dict] = {}
        for row in rows:
            current = latest.get(row["id"])
            if current is None or (row.get(time_field) or "") >= (current.get(time_field) or ""):
                latest[row["id"]] = row
        return latest

    def _verification_statuses(self, since_day: date) -> dict[str, str]:
        """News id -> latest verification status, from the per-cluster records."""
        statuses: dict[str, tuple[str, str]] = {}
        for row in self._rows(self._files(NEWS_VERIFIED, since_day)):
            as_of = row.get("as_of") or ""
            for news_id, status in zip(row.get("status_ids") or [], row.get("id_statuses") or []):
                if news_id not in statuses or as_of >= statuses[news_id][0]:
                    statuses[news_id] = (as_of, status)
        return {news_id: status for news_id, (_, status) in statuses.items()}
