"""A hand-built panel of 260 sessions with 3 pm snapshots on its last five, for the live feature tests (story B7)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from feature_fixtures import black76, make_panel, session_days, zigzag_closes

from fno.research_data.events import Event
from fno.research_data.quote_snapshots import CutoffSnapshot, LiveQuote
from fno.research_engine.features import DecisionContext, ResearchData

DAYS = session_days(260, date(2025, 1, 1))
DAY = DAYS[258]  # an even index: the previous close is the zigzag's upper value, so every return is +-0.01
EXPIRY = DAY + timedelta(days=41)
YEARS = 41 / 365
SPOT, FORWARD, SIGMA, RATE = 20000.0, 20100.0, 0.17, 0.065
CUTOFF = time(15, 0)
VIX = [float(10 + i % 7) for i in range(260)]  # previous 250 values' median is 13.0


def quotes(day: date, prices: dict | None = None, valid: bool = True, spread: float = 1.0) -> tuple[LiveQuote, ...]:
    """Valid two-sided quotes of EXPIRY around Black-76 prices (forward 20100, 17% volatility): mid = model price."""
    years = (EXPIRY - day).days / 365
    out = []
    for strike in (19900.0, 20000.0, 20100.0):
        for kind in ("CE", "PE"):
            price = (prices or {}).get((strike, kind), black76(FORWARD, strike, years, SIGMA, kind, RATE))
            out.append(LiveQuote(EXPIRY, strike, kind, price - spread / 2, price + spread / 2, valid))
    return tuple(out)


def snapshot(day: date, finished: time = time(14, 56), vix: float | None = 14.0, **kwargs) -> CutoffSnapshot:
    return CutoffSnapshot(day, datetime.combine(day, finished), SPOT, vix, quotes(day, **kwargs))


def live_data(snapshots: dict | None = None) -> ResearchData:
    panel = make_panel(DAYS, zigzag_closes(260), vix=VIX)
    events = (Event(DAY + timedelta(days=10), "rbi_policy", True, DAY - timedelta(days=30), "known meeting"),)
    default = {d: snapshot(d) for d in DAYS[-5:]}
    return ResearchData(panel, events, default if snapshots is None else snapshots)


def live_context(day: date = DAY) -> DecisionContext:
    return DecisionContext(EXPIRY, day + timedelta(days=1), EXPIRY - timedelta(days=21))
