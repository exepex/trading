"""Index closes from Yahoo Finance's public chart API (story A17e): one class for every index without a timely official
file, and the history before an official file starts.

Owner rule 50a79a43 (21 Oct 2026): a source's redistribution terms do not block a download for private research; the
values live in Drive only (`private`). Its rule 2 is kept here: **a block is a stop, never a puzzle**. One plain GET,
redirects not followed; an answer of HTTP 401, 403 or 429, any redirect (Yahoo's consent page arrives that way) or an
answer that is not chart JSON (a consent, crumb or CAPTCHA page) raises `YahooBlocked`, which the collector reports as
that cue's failure for the run. Nothing retries it with a cookie, a crumb, another user agent or another address; the
next scheduled run asks once more, the same way.

Yahoo is an aggregator, not the index owner: where an official file exists it is preferred (`index_reader.py`) and
compared (`pair_checks.py`); an index with no official file is `unverified (Yahoo only)`.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import requests

from .markets import MarketClose
from .source import TIMEOUT_SECONDS, CueRequest, CueValue, GlobalCueSource, positive

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={start}&period2={end}&interval=1d"
BLOCK_STATUSES = (401, 403, 429)
BLOCKED = "{cue}: Yahoo {what}; stopped for this run, never retried another way"
UNVERIFIED = "unverified (Yahoo only)"


class YahooBlocked(requests.RequestException):
    """Yahoo refused or redirected the request, or answered with a page that is not chart data."""


class YahooChartSource(GlobalCueSource):
    unit, private, may_hold_unfinished = "index points", True, True
    first_value_date = date(2019, 1, 1)

    def __init__(self, cue: str, symbol: str, market: MarketClose, max_age_days: int, verified: bool):
        """`verified`: an official file of the same index exists to compare against."""
        self.cue, self.symbol, self.market, self.max_age_days = cue, symbol, market, max_age_days
        self.date_zone, self.verified = market.zone, verified
        self.dataset = f"yahoo/indices/{symbol.lstrip('^').lower()}-chart"
        label = "" if verified else f"; {UNVERIFIED}"
        self.publisher = f"Yahoo Finance chart data ({symbol}), an aggregator, not the index owner{label}"

    def requests(self, start: date, end: date) -> list[CueRequest]:
        first = int(datetime.combine(start, time(), tzinfo=UTC).timestamp())
        last = int(datetime.combine(end + timedelta(days=1), time(), tzinfo=UTC).timestamp())
        url = YAHOO_CHART.format(symbol=self.symbol.replace("^", "%5E"), start=first, end=last)
        return [CueRequest(f"{self.dataset.rsplit('/', 1)[-1]}_{start:%Y%m%d}_{end:%Y%m%d}.json", url)]

    def download(self, session: requests.Session, request: CueRequest) -> bytes:
        response = session.get(request.url, timeout=TIMEOUT_SECONDS, allow_redirects=False)
        if response.status_code in BLOCK_STATUSES or response.is_redirect:
            raise YahooBlocked(BLOCKED.format(cue=self.cue, what=f"answered HTTP {response.status_code}"))
        response.raise_for_status()
        if not response.content.lstrip().startswith(b"{"):
            raise YahooBlocked(BLOCKED.format(cue=self.cue, what="sent a page, not chart data (consent or CAPTCHA?)"))
        return response.content

    def parse(self, data: bytes) -> list[CueValue]:
        result = chart_result(data, self.cue)
        zone = ZoneInfo(result["meta"]["exchangeTimezoneName"])
        closes = result["indicators"]["quote"][0]["close"]
        if not result.get("timestamp") or len(closes) != len(result["timestamp"]):
            raise ValueError(f"{self.cue}: no timestamps, or not one close per timestamp")
        pairs = [
            (datetime.fromtimestamp(stamp, zone).date(), close)
            for stamp, close in zip(result["timestamp"], closes, strict=True)
            if close is not None  # a session Yahoo has no close for yet
        ]
        twice = {day for day, n in Counter(day for day, _ in pairs).items() if n > 1}
        values = [CueValue(day, positive(close, day.isoformat(), True)) for day, close in pairs if day not in twice]
        return sorted(values, key=lambda v: v.value_date)  # a date given twice is left out, never guessed: a gap

    def available_at(self, value_date: date) -> datetime:
        return self.market.available_at(value_date)


def chart_result(data: bytes, cue: str) -> dict:
    try:
        document = json.loads(data)
        result = document["chart"]["result"][0]
        result["meta"]["exchangeTimezoneName"], result["indicators"]["quote"][0]["close"]  # noqa: B018 - shape check
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"{cue}: not Yahoo's chart answer ({type(exc).__name__})") from exc
    return result
