"""A tiny synthetic panel: one expiry, strikes 100 points apart, prices set per day by hand."""

from __future__ import annotations

from datetime import date, timedelta

from fno.research_data.panel_reader import FutureQuote, NiftyPanel, OptionQuote, SessionClose
from fno.research_engine.cycle_costs import CycleTerms
from fno.research_engine.cycles import Cycle

EXPIRY = date(2025, 3, 27)
ENTRY, EXIT = date(2025, 2, 13), date(2025, 3, 6)
DAYS = [ENTRY + timedelta(days=i) for i in range(0, 22)]
CHARGES = {"brokerage_per_order": 20.0, "stt_sell_pct": 0.15, "stt_exercise_pct": 0.15, "exchange_txn_pct": 0.03503,
           "sebi_per_crore": 10, "ipft_per_crore": 50, "stamp_duty_buy_pct": 0.003, "gst_pct": 18}  # fmt: skip
STRIKES = [float(k) for k in range(21000, 25100, 100)]


def flat_prices(spot: float) -> dict[tuple[float, str], float]:
    """A simple, arbitrage-free-enough price per contract: intrinsic plus a time value falling away from spot."""
    out = {}
    for k in STRIKES:
        time_value = max(5.0, 200.0 - abs(k - spot) * 0.15)
        out[(k, "CE")] = max(spot - k, 0.0) + time_value
        out[(k, "PE")] = max(k - spot, 0.0) + time_value
    return out


def quotes(prices: dict, untraded: set = frozenset(), unlisted: set = frozenset()) -> tuple[OptionQuote, ...]:
    return tuple(OptionQuote(EXPIRY, k, kind, p, p * 0.9, 0 if (k, kind) in untraded else 10, 100)
                 for (k, kind), p in prices.items() if (k, kind) not in unlisted)  # fmt: skip


def panel(day_prices: dict[date, tuple[float, dict, set]], spot: float = 23000.0) -> NiftyPanel:
    """`day_prices`: day -> (spot, prices, untraded contracts)."""
    sessions, options, futures = [], {}, {}
    for day in DAYS:
        s, prices, untraded = day_prices.get(day, (spot, flat_prices(spot), set()))
        sessions.append(SessionClose(day, "regular", s, None))
        options[day] = quotes(prices, untraded)
        futures[day] = (FutureQuote(EXPIRY, s, s, 10, 100),)
    return NiftyPanel(tuple(sessions), options, futures)


def cycle() -> Cycle:
    return Cycle(EXPIRY, ENTRY - timedelta(days=1), ENTRY, EXIT)


def terms(lot: int = 65, pad: float = 1.0, widths=(300.0, 200.0, 100.0)) -> CycleTerms:
    return CycleTerms(lot, CHARGES, pad, 10_000.0, widths)
