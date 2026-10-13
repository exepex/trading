"""Fixture data for the forecast tests (stories G1-G3): a 2026 calendar, closes-only histories and one option day."""

from __future__ import annotations

from datetime import date

from fno.forecast.history import ForecastHistory
from fno.forecast.iv30 import PanelAtmIv30
from fno.forecast.targets import trading_days
from fno.research_data.calendar import CsvSessionCalendar
from fno.research_data.panel_reader import FutureQuote, NiftyPanel, OptionQuote, SessionClose
from fno.research_engine.implied_vol import Black76, OptionPricing

RATE = 0.065
CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n2026-01-26,holiday,Republic Day,https://example.invalid\n"
)
ESTIMATOR = PanelAtmIv30(Black76(), RATE)
DAYS = trading_days(CALENDAR, date(2026, 1, 1), date(2026, 12, 31))


def closes_history(nifty: dict[int, float], default: float = 100.0, count: int = 60) -> ForecastHistory:
    """A closes-only history over the calendar's first `count` trading days; `nifty` sets closes by day index."""
    sessions = tuple(SessionClose(day, "regular", nifty.get(i, default), 15.0) for i, day in enumerate(DAYS[:count]))
    return ForecastHistory(NiftyPanel(sessions, {}, {}), CALENDAR, ESTIMATOR)


# One option day: Mon 2 Mar 2026, NIFTY 22,000; monthly expiries 18 Mar (16 days, future 22,050) and 15 Apr (44 days,
# future 22,120); Black-76 closes at 12% / 14% (18 Mar call / put) and 15% (15 Apr): IV30 = 14.4937 points (test_iv30).
OPTION_DAY, SPOT = date(2026, 3, 2), 22000.0
E1, E2 = date(2026, 3, 18), date(2026, 4, 15)
FUTURES = {E1: 22050.0, E2: 22120.0}
VOLS = {(E1, "CE"): 0.12, (E1, "PE"): 0.14, (E2, "CE"): 0.15, (E2, "PE"): 0.15}


def _price(expiry: date, strike: float, kind: str) -> float:
    pricing = OptionPricing(0.0, FUTURES[expiry], strike, kind, (expiry - OPTION_DAY).days / 365, RATE)
    return round(Black76().price(pricing, VOLS.get((expiry, kind), 0.2)), 6)


def option_day_history() -> ForecastHistory:
    quotes = tuple(
        OptionQuote(e, k, kind, _price(e, k, kind), 0.0, 1000, 1)
        for e in (E1, E2)
        for k in (21950.0, 22000.0, 22050.0)
        for kind in ("CE", "PE")
    )
    futures = tuple(FutureQuote(e, f, f, 500, 1) for e, f in FUTURES.items())
    session = SessionClose(OPTION_DAY, "regular", SPOT, 15.0)
    return ForecastHistory(NiftyPanel((session,), {OPTION_DAY: quotes}, {OPTION_DAY: futures}), CALENDAR, ESTIMATOR)
