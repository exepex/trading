"""Intraday prices. YahooPriceFeed works today without a broker; a Groww feed can replace it later."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote

import requests

from ...models import IST
from ...providers.base import YAHOO_SYMBOLS
from ..models import Candle

YAHOO_SPARK_URL = "https://query1.finance.yahoo.com/v8/finance/spark"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
YAHOO_BATCH_SIZE = 20
YAHOO_EXCHANGE_SUFFIX = ".NS"
CANDLE_INTERVAL = "5m"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"


@dataclass(frozen=True)
class DayQuote:
    symbol: str
    last_price: float
    previous_close: float


class IntradayPriceFeed(ABC):
    """What the scanner needs from any intraday price source."""

    @abstractmethod
    def day_quotes(self, symbols: list[str]) -> dict[str, DayQuote]:
        """Latest price and previous close for many symbols at once."""

    @abstractmethod
    def candles(self, symbol: str) -> list[Candle]:
        """Today's 5-minute candles, oldest first."""


def yahoo_symbol(symbol: str) -> str:
    return YAHOO_SYMBOLS.get(symbol, f"{symbol}{YAHOO_EXCHANGE_SUFFIX}")


class YahooPriceFeed(IntradayPriceFeed):
    def __init__(self, session: requests.Session | None = None, timeout: int = 20):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.timeout = timeout

    def _get(self, url: str, params: dict) -> dict:
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def day_quotes(self, symbols: list[str]) -> dict[str, DayQuote]:
        by_yahoo = {yahoo_symbol(s): s for s in symbols}
        names = list(by_yahoo)
        quotes: dict[str, DayQuote] = {}
        for start in range(0, len(names), YAHOO_BATCH_SIZE):
            batch = names[start : start + YAHOO_BATCH_SIZE]
            payload = self._get(
                YAHOO_SPARK_URL, {"symbols": ",".join(batch), "range": "1d", "interval": CANDLE_INTERVAL}
            )
            quotes.update(parse_spark(payload, by_yahoo))
        return quotes

    def candles(self, symbol: str) -> list[Candle]:
        url = YAHOO_CHART_URL.format(symbol=quote(yahoo_symbol(symbol), safe=""))
        payload = self._get(url, {"range": "1d", "interval": CANDLE_INTERVAL})
        return parse_chart_candles(payload)


def parse_spark(payload: dict, by_yahoo: dict[str, str]) -> dict[str, DayQuote]:
    quotes = {}
    for ysym, series in payload.items():
        closes = [c for c in (series.get("close") or []) if c is not None]
        prev = series.get("previousClose") or series.get("chartPreviousClose")
        if closes and prev and ysym in by_yahoo:
            sym = by_yahoo[ysym]
            quotes[sym] = DayQuote(sym, float(closes[-1]), float(prev))
    return quotes


def parse_chart_candles(payload: dict) -> list[Candle]:
    result = (payload.get("chart", {}).get("result") or [None])[0]
    if not result:
        return []
    q = result["indicators"]["quote"][0]
    out = []
    for i, ts in enumerate(result.get("timestamp") or []):
        values = [q[k][i] for k in ("open", "high", "low", "close")]
        if any(v is None for v in values):
            continue
        out.append(
            Candle(
                start=datetime.fromtimestamp(ts, IST),
                open=float(values[0]),
                high=float(values[1]),
                low=float(values[2]),
                close=float(values[3]),
                volume=float(q["volume"][i] or 0),
            )
        )
    return out
