"""Market-adjusted event moves of 2019-2021 only, for the within-week correlation (PROTOCOL.md section 7, amendment 1
section D9). Refuses any other year: 2022-2026 event moves stay unread."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from .bhav import DaySummary
from .clusters import bootstrap_interval, grouped, icc_anova, kish_count
from .events import Event
from .rules import CORRELATION_YEARS


class OutsideCorrelationYears(ValueError):
    """An event move outside 2019-2021 was asked for: the protocol forbids reading it."""


def market_adjusted_move(
    event: Event, entry: DaySummary, reaction: DaySummary, nifty_entry: float, nifty_reaction: float
) -> float | None:
    """m = ln(F_R / F_entry) - ln(NIFTY_R / NIFTY_entry), F the future with the nearest expiry on or after R."""
    if event.reaction.year not in CORRELATION_YEARS:
        raise OutsideCorrelationYears(f"{event.symbol} {event.reaction}: only 2019-2021 moves may be read")
    before = entry.near_future(event.symbol, on_or_after=event.reaction)
    if before is None:
        return None
    after = next((f for f in reaction.futures.get(event.symbol, []) if f.expiry == before.expiry), None)
    if after is None or before.close <= 0 or after.close <= 0 or nifty_entry <= 0 or nifty_reaction <= 0:
        return None
    return math.log(after.close / before.close) - math.log(nifty_reaction / nifty_entry)


@dataclass(frozen=True)
class Correlation:
    events: int
    clusters: int
    rho_move: float | None
    rho_move_interval: tuple[float | None, float | None]
    rho_abs: float | None
    rho_abs_interval: tuple[float | None, float | None]
    kish: float


def within_week_correlation(moves: list[tuple[tuple, float]]) -> Correlation:
    """ICC of m and of |m| by cluster, with cluster-bootstrap 90% intervals and Kish's effective count (|m|'s ICC)."""
    signed = grouped(moves)
    absolute = grouped([(key, abs(m)) for key, m in moves])
    rho_abs = icc_anova(absolute)
    return Correlation(
        events=len(moves),
        clusters=len(signed),
        rho_move=icc_anova(signed),
        rho_move_interval=bootstrap_interval(signed),
        rho_abs=rho_abs,
        rho_abs_interval=bootstrap_interval(absolute),
        kish=kish_count([len(g) for g in signed], rho_abs),
    )


def correlation_events(events: list[Event], first: date | None = None) -> list[Event]:
    return [e for e in events if e.reaction.year in CORRELATION_YEARS and (first is None or e.reaction >= first)]
