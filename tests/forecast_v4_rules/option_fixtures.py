"""Fixture packs' quote shapes for V4 and V5 (G10's `ChainQuote` on main): option mids priced by Black-76 at a known
volatility and forward, so the terms must recover them."""

from dataclasses import replace as copy
from datetime import date, datetime, time

from fno.models import IST
from fno.research_engine.implied_vol import Black76, OptionPricing
from fno.v4_pack.model import ChainQuote

RATE = 0.065
D = date(2026, 10, 27)  # Tue: the October monthly's expiry day itself
WEEKLY = date(2026, 11, 3)  # 5 scored sessions and 7 calendar days after D (v4_golden.json's case)
MONTHLY = date(2026, 11, 23)  # November's monthly (24 Nov is a holiday)
LISTED = [D, WEEKLY, date(2026, 11, 9), date(2026, 11, 17), MONTHLY, date(2026, 12, 1), date(2026, 12, 29)]
TRADED = datetime.combine(D, time(14, 29), IST)
SEEN = datetime.combine(D, time(14, 31), IST)


def mid_at(forward: float, strike: float, kind: str, expiry: date, sigma: float) -> float:
    years = (expiry - D).days / 365
    return Black76().price(OptionPricing(0.0, forward, strike, kind, years, RATE), sigma)


def chain(expiry: date, forward: float, sigma: float, strikes=(25900.0, 26000.0, 26100.0), half_spread=0.004,
          traded=TRADED) -> list[ChainQuote]:  # fmt: skip
    """Both legs at every strike, two-sided around the model mid (spread 0.8% of mid by default)."""
    quotes = []
    for strike in strikes:
        for kind in ("CE", "PE"):
            mid = mid_at(forward, strike, kind, expiry, sigma)
            quotes.append(ChainQuote(expiry, strike, kind, mid * (1 - half_spread), mid * (1 + half_spread), mid,
                                     traded, SEEN))  # fmt: skip
    return quotes


def replace(quotes: list[ChainQuote], strike: float, kind: str, **changes) -> list[ChainQuote]:
    return [copy(q, **changes) if (q.strike, q.kind) == (strike, kind) else q for q in quotes]
