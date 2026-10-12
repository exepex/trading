"""The tradable F&O universe for the day, and per-scan snapshots of every underlying in it."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date

from .feeds.nse_feed import NseLiveFeed, OpenInterestMove
from .feeds.participant_oi import FiiPositioning, load_fii_positioning
from .feeds.price_feed import DayQuote
from .models import UnderlyingSnapshot

log = logging.getLogger(__name__)


@dataclass
class ReferenceData:
    """Refreshed once per trading day."""

    loaded_on: date
    lot_sizes: dict[str, int] = field(default_factory=dict)
    banned: set[str] = field(default_factory=set)
    holidays: set[date] = field(default_factory=set)
    industries: dict[str, str] = field(default_factory=dict)  # NSE industry per stock
    fii: FiiPositioning | None = None  # foreign investors' index positioning over recent sessions

    @property
    def symbols(self) -> list[str]:
        return sorted(self.lot_sizes)

    @classmethod
    def load(cls, feed: NseLiveFeed, today: date) -> ReferenceData:
        return cls(
            loaded_on=today,
            lot_sizes=feed.lot_sizes(),
            banned=feed.ban_list(),
            holidays=feed.trading_holidays(),
            industries=feed.industries(),
            fii=_fii_positioning(feed, today),
        )


def _fii_positioning(feed: NseLiveFeed, today: date) -> FiiPositioning | None:
    try:
        return load_fii_positioning(feed.archive_text_or_none, today)
    except Exception as exc:  # noqa: BLE001 - helpful context, never a reason to stop the day
        log.warning("FII positioning unavailable: %s", exc)
        return None


def build_snapshots(
    symbols: list[str], quotes: dict[str, DayQuote], oi_moves: dict[str, OpenInterestMove]
) -> dict[str, UnderlyingSnapshot]:
    """Join price quotes with futures open-interest moves. Symbols without a price are skipped."""
    snapshots = {}
    for symbol in symbols:
        quote = quotes.get(symbol)
        if quote is None:
            continue
        move = oi_moves.get(symbol)
        snapshots[symbol] = UnderlyingSnapshot(
            symbol=symbol,
            last_price=quote.last_price,
            previous_close=quote.previous_close,
            oi_change_pct=move.oi_change_pct if move else None,
            traded_value=move.traded_value if move else 0.0,
        )
    return snapshots


def choose_expiry(expiries: list[date], today: date, min_days_to_expiry: int) -> date | None:
    """Nearest expiry far enough away that the holding rules never touch expiry day."""
    return next((e for e in sorted(expiries) if (e - today).days >= min_days_to_expiry), None)
