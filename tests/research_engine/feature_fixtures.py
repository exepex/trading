"""Small hand-built NIFTY panels and decision contexts for the feature tests (story B1)."""

from __future__ import annotations

import math
from datetime import date, timedelta

from fno.constants import OPTION_CALL, SESSION_REGULAR
from fno.research_data.panel_reader import FutureQuote, NiftyPanel, OptionQuote, SessionClose
from fno.research_engine.features import DecisionContext, ResearchData

START = date(2025, 1, 1)
EXPIRY = date(2025, 3, 27)
RATE = 0.065


def norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def black76(forward: float, strike: float, years: float, sigma: float, kind: str, rate: float = RATE) -> float:
    """Textbook Black-76, written here independently of fno/research_engine/implied_vol.py."""
    d1 = (math.log(forward / strike) + sigma * sigma * years / 2) / (sigma * math.sqrt(years))
    d2 = d1 - sigma * math.sqrt(years)
    call = forward * norm_cdf(d1) - strike * norm_cdf(d2)
    put = strike * norm_cdf(-d2) - forward * norm_cdf(-d1)
    return math.exp(-rate * years) * (call if kind == OPTION_CALL else put)


def session_days(count: int, start: date = START) -> list[date]:
    """`count` consecutive calendar days used as sessions (the features never look at weekdays)."""
    return [start + timedelta(days=i) for i in range(count)]


def zigzag_closes(count: int, step: float = 0.01, first: float = 20000.0) -> list[float]:
    """Closes whose daily log returns alternate +step, -step: realised volatility = step * sqrt(252) exactly."""
    return [first * math.exp(step if i % 2 else 0.0) for i in range(count)]


def make_panel(
    days: list[date],
    closes: list[float | None],
    vix: list[float | None] | None = None,
    options: dict[date, list[OptionQuote]] | None = None,
    futures: dict[date, list[FutureQuote]] | None = None,
    session: str = SESSION_REGULAR,
) -> NiftyPanel:
    vix = vix or [15.0] * len(days)
    sessions = tuple(SessionClose(d, session, c, v) for d, c, v in zip(days, closes, vix))
    return NiftyPanel(sessions, {d: tuple(q) for d, q in (options or {}).items()}, {
        d: tuple(q) for d, q in (futures or {}).items()
    })  # fmt: skip


def chain(strikes: list[float], prices: dict[tuple[float, str], float], volume: int = 100) -> list[OptionQuote]:
    """Option quotes of EXPIRY at `strikes`; legs missing from `prices` are listed at 5.0 with volume."""
    return [
        OptionQuote(EXPIRY, k, kind, prices.get((k, kind), 5.0), 0.0, volume, 1000)
        for k in strikes
        for kind in ("CE", "PE")
    ]


def future(close: float, volume: int = 100, expiry: date = EXPIRY) -> FutureQuote:
    return FutureQuote(expiry, close, close, volume, 1000)


def context(entry: date, exit_day: date, expiry: date = EXPIRY) -> DecisionContext:
    return DecisionContext(expiry, entry, exit_day)


def data(panel: NiftyPanel, events=()) -> ResearchData:
    return ResearchData(panel, tuple(events))
