"""Latest prices of a few underlyings, often (every 20 seconds), for the sudden-move detector.

Only an official broker feed may be asked this often: Groww (`get_ltp`, up to 50 symbols per call). There is no free
fallback on purpose: polling NSE or Yahoo every 20 seconds would get the owner's IP blocked."""

from __future__ import annotations

from abc import ABC, abstractmethod

GROWW_SYMBOL_PREFIX = "NSE_"
GROWW_BATCH = 50
GROWW_INDEX_SYMBOLS = {"NIFTY": "NIFTY", "BANKNIFTY": "BANKNIFTY", "FINNIFTY": "FINNIFTY"}  # verify with groww-check


class LivePriceSource(ABC):
    @abstractmethod
    def prices(self, symbols: list[str]) -> dict[str, float]:
        """Latest traded price per symbol; symbols it cannot price are left out."""


def parse_groww_ltp(payload: dict, prefix: str = GROWW_SYMBOL_PREFIX) -> dict[str, float]:
    """{"NSE_RELIANCE": 2500.5} or {"NSE_RELIANCE": {"ltp": 2500.5}} -> {"RELIANCE": 2500.5}."""
    out = {}
    for key, value in (payload or {}).items():
        price = value.get("ltp") if isinstance(value, dict) else value
        if isinstance(price, int | float) and price > 0:
            out[key.removeprefix(prefix)] = float(price)
    return out


class GrowwLivePrices(LivePriceSource):
    def __init__(self, api_provider):
        """api_provider: anything with `.api` (the signed-in Groww SDK client), e.g. GrowwProvider."""
        self.api_provider = api_provider

    def prices(self, symbols: list[str]) -> dict[str, float]:
        api = self.api_provider.api
        names = [GROWW_SYMBOL_PREFIX + GROWW_INDEX_SYMBOLS.get(s, s) for s in symbols]
        back = {GROWW_SYMBOL_PREFIX + GROWW_INDEX_SYMBOLS.get(s, s): s for s in symbols}
        out = {}
        for start in range(0, len(names), GROWW_BATCH):
            batch = tuple(names[start : start + GROWW_BATCH])
            payload = api.get_ltp(exchange_trading_symbols=batch, segment=api.SEGMENT_CASH)
            payload = payload.get("payload", payload) if isinstance(payload, dict) else {}
            for name, price in parse_groww_ltp(payload, "").items():
                if name in back:
                    out[back[name]] = price
        return out
