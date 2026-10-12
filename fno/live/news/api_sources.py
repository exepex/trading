"""News APIs on free plans: Finnhub (world market headlines), Marketaux (Indian stocks, tagged) and AskNews
(world events). Each is skipped when its key is not set. Keys travel in headers, never in logged URLs."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import requests

from ...constants import ENV_ASKNEWS_API_KEY, ENV_FINNHUB_API_KEY, ENV_MARKETAUX_API_TOKEN
from .models import NewsItem
from .source import NewsSource

REQUEST_TIMEOUT_SECONDS = 20
FINNHUB_SOURCE = "Finnhub"
FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/news"
FINNHUB_KEY_HEADER = "X-Finnhub-Token"
FINNHUB_CATEGORY = "general"
MARKETAUX_SOURCE = "Marketaux"
MARKETAUX_NEWS_URL = "https://api.marketaux.com/v1/news/all"
MARKETAUX_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
MARKETAUX_INDIA_EXCHANGES = (".NS", ".BO")
ASKNEWS_SOURCE = "AskNews"
ASKNEWS_SEARCH_URL = "https://api.asknews.app/v1/news/search"
ASKNEWS_DEFAULT_QUERY = "markets oil war central bank tariffs India economy"
ASKNEWS_ARTICLES = 10
FIRST_LOOKBACK = timedelta(minutes=30)  # how far back the first request of a run looks


HTTP_ERROR_TEMPLATE = "{source} answered HTTP {status}"  # never the URL: Marketaux's token travels in it


def _check(resp: requests.Response, source: str) -> None:
    if not resp.ok:
        raise requests.HTTPError(HTTP_ERROR_TEMPLATE.format(source=source, status=resp.status_code), response=resp)


def _key(env_name: str) -> str | None:
    return os.environ.get(env_name) or None


def _iso(text: str | None) -> datetime | None:
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


class FinnhubNewsSource(NewsSource):
    """General market news (world). Asks only for items newer than the last id it saw."""

    name = FINNHUB_SOURCE

    def __init__(self, api_key: str, session: requests.Session):
        self.api_key = api_key
        self.session = session
        self._last_id = 0

    def fetch(self, now: datetime) -> list[NewsItem]:
        params = {"category": FINNHUB_CATEGORY, "minId": self._last_id}
        resp = self.session.get(
            FINNHUB_NEWS_URL, params=params, headers={FINNHUB_KEY_HEADER: self.api_key}, timeout=REQUEST_TIMEOUT_SECONDS
        )
        _check(resp, self.name)
        rows = resp.json() or []
        self._last_id = max([self._last_id] + [int(r.get("id") or 0) for r in rows])
        return [
            NewsItem(
                source=self.name,
                title=(r.get("headline") or "").strip(),
                url=r.get("url") or "",
                published_at=datetime.fromtimestamp(r["datetime"], UTC) if r.get("datetime") else None,
                summary=(r.get("summary") or "").strip(),
            )
            for r in rows
            if r.get("headline")
        ]


def indian_symbols(entities: list[dict]) -> tuple[str, ...]:
    """Marketaux tags RELIANCE.NS / 500325.BO style symbols; keep the NSE-style part of Indian ones."""
    out = []
    for entity in entities or []:
        symbol = entity.get("symbol") or ""
        for suffix in MARKETAUX_INDIA_EXCHANGES:
            if symbol.endswith(suffix) and not symbol[: -len(suffix)].isdigit():
                out.append(symbol[: -len(suffix)])
    return tuple(dict.fromkeys(out))


class MarketauxNewsSource(NewsSource):
    """Indian market news with tagged stocks. Asks only for articles published since its last request."""

    name = MARKETAUX_SOURCE

    def __init__(self, api_token: str, session: requests.Session, countries: str = "in"):
        self.api_token = api_token
        self.session = session
        self.countries = countries
        self._since: datetime | None = None

    def fetch(self, now: datetime) -> list[NewsItem]:
        since = self._since or now - FIRST_LOOKBACK
        params = {
            "countries": self.countries,
            "language": "en",
            "filter_entities": "true",
            "published_after": since.astimezone(UTC).strftime(MARKETAUX_TIME_FORMAT),
            "api_token": self.api_token,
        }
        resp = self.session.get(MARKETAUX_NEWS_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        _check(resp, self.name)
        self._since = now
        return [
            NewsItem(
                source=self.name,
                title=(a.get("title") or "").strip(),
                url=a.get("url") or "",
                published_at=_iso(a.get("published_at")),
                summary=(a.get("description") or a.get("snippet") or "").strip(),
                symbols=indian_symbols(a.get("entities")),
            )
            for a in (resp.json() or {}).get("data", [])
            if a.get("title")
        ]


class AskNewsSource(NewsSource):
    """World events that move indices (war, oil, central banks, tariffs), from AskNews' latest-news search."""

    name = ASKNEWS_SOURCE

    def __init__(self, api_key: str, session: requests.Session, query: str = ASKNEWS_DEFAULT_QUERY):
        self.api_key = api_key
        self.session = session
        self.query = query
        self._since: datetime | None = None

    def fetch(self, now: datetime) -> list[NewsItem]:
        since = self._since or now - FIRST_LOOKBACK
        params = {
            "query": self.query,
            "n_articles": ASKNEWS_ARTICLES,
            "return_type": "dicts",
            "method": "kw",
            "start_timestamp": int(since.timestamp()),
            "historical": "false",
        }
        resp = self.session.get(
            ASKNEWS_SEARCH_URL,
            params=params,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        _check(resp, self.name)
        self._since = now
        return [
            NewsItem(
                source=self.name,
                title=(a.get("eng_title") or a.get("title") or "").strip(),
                url=a.get("article_url") or "",
                published_at=_iso(a.get("pub_date")),
                summary=(a.get("summary") or "").strip(),
            )
            for a in (resp.json() or {}).get("as_dicts") or []
            if a.get("eng_title") or a.get("title")
        ]


def api_sources_from_environment(session: requests.Session, enabled: dict[str, dict]) -> list[NewsSource]:
    """The API sources whose keys are set and which config leaves enabled."""
    builders = {
        "finnhub": (ENV_FINNHUB_API_KEY, lambda key, opts: FinnhubNewsSource(key, session)),
        "marketaux": (
            ENV_MARKETAUX_API_TOKEN,
            lambda key, opts: MarketauxNewsSource(key, session, opts.get("countries", "in")),
        ),
        "asknews": (
            ENV_ASKNEWS_API_KEY,
            lambda key, opts: AskNewsSource(key, session, opts.get("query", ASKNEWS_DEFAULT_QUERY)),
        ),
    }
    sources = []
    for name, (env_name, build) in builders.items():
        opts = enabled.get(name)
        key = _key(env_name)
        if opts is not None and opts.get("enabled", True) and key:
            sources.append(build(key, opts))
    return sources
