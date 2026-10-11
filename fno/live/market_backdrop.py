"""Market-wide context for one scan: sector indices, global markets, India VIX and breadth across F&O names."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..constants import INDEX_UNDERLYINGS
from .feeds.price_feed import DayQuote, IntradayPriceFeed
from .models import UnderlyingSnapshot

# NSE industry (from the NIFTY 500 list) -> the sector index that best tracks it, as a Yahoo symbol.
SECTOR_INDEX_BY_INDUSTRY = {
    "Financial Services": "NIFTY_FIN_SERVICE.NS",
    "Information Technology": "^CNXIT",
    "Automobile and Auto Components": "^CNXAUTO",
    "Healthcare": "^CNXPHARMA",
    "Fast Moving Consumer Goods": "^CNXFMCG",
    "Metals & Mining": "^CNXMETAL",
    "Realty": "^CNXREALTY",
    "Oil Gas & Consumable Fuels": "^CNXENERGY",
    "Power": "^CNXENERGY",
    "Capital Goods": "^CNXINFRA",
    "Construction": "^CNXINFRA",
    "Construction Materials": "^CNXINFRA",
    "Telecommunication": "^CNXINFRA",
    "Media Entertainment & Publication": "^CNXMEDIA",
}
GLOBAL_MARKETS = ("ES=F", "NQ=F", "^N225", "^HSI")  # S&P 500 and Nasdaq futures, Nikkei, Hang Seng
INDIA_VIX = "^INDIAVIX"


@dataclass
class MarketBackdrop:
    sector_change_pct: dict[str, float] = field(default_factory=dict)  # sector index symbol -> today's % move
    global_change_pct: float | None = None  # average % move of the global markets
    vix_change_pct: float | None = None
    breadth: float | None = None  # (advancers - decliners) / all F&O stocks, -1..+1
    advancers: int = 0
    decliners: int = 0

    def sector_change_for(self, industry: str | None) -> float | None:
        index = SECTOR_INDEX_BY_INDUSTRY.get(industry or "")
        return self.sector_change_pct.get(index) if index else None


def change_pct(quote: DayQuote | None) -> float | None:
    if quote is None or not quote.previous_close:
        return None
    return (quote.last_price / quote.previous_close - 1) * 100


def market_breadth(snapshots: dict[str, UnderlyingSnapshot]) -> tuple[float | None, int, int]:
    moves = [s.day_change_pct for sym, s in snapshots.items() if sym not in INDEX_UNDERLYINGS and s.day_change_pct]
    advancers, decliners = sum(m > 0 for m in moves), sum(m < 0 for m in moves)
    total = advancers + decliners
    return ((advancers - decliners) / total if total else None), advancers, decliners


def build_market_backdrop(price_feed: IntradayPriceFeed, snapshots: dict[str, UnderlyingSnapshot]) -> MarketBackdrop:
    symbols = sorted(set(SECTOR_INDEX_BY_INDUSTRY.values()) | set(GLOBAL_MARKETS) | {INDIA_VIX})
    quotes = price_feed.day_quotes(symbols)
    global_moves = [m for m in (change_pct(quotes.get(s)) for s in GLOBAL_MARKETS) if m is not None]
    breadth, advancers, decliners = market_breadth(snapshots)
    return MarketBackdrop(
        sector_change_pct={
            s: m for s in set(SECTOR_INDEX_BY_INDUSTRY.values()) if (m := change_pct(quotes.get(s))) is not None
        },
        global_change_pct=sum(global_moves) / len(global_moves) if global_moves else None,
        vix_change_pct=change_pct(quotes.get(INDIA_VIX)),
        breadth=breadth,
        advancers=advancers,
        decliners=decliners,
    )
