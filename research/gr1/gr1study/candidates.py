"""GR1's candidates C1-C11 (protocol section 6). Each turns a row into its conditioner vector `x` (intercept first),
or None when an input is missing that day (the day is dropped for that candidate, and reported; section 7). Every
input is the one known at the issue time (section 3); `Context` holds them, built by `inputs.py` from real data or by
the tests from synthetic data."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date

from .rows import Row

C11_POOL = ("C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10")
CUES = ("sp500", "us10y", "usdinr_rbi")
NIFTY = "NIFTY"


@dataclass(frozen=True)
class Context:
    vix: dict[date, float]  # India VIX close of each session
    previous_session: Callable[[date], date]
    events: dict[date, date]  # RBI policy, budget and election-result day -> the day its date was announced
    expiries: dict[str, frozenset[date]]  # each index's option expiry dates
    cue_move: Callable[[str, date], float | None]  # |last-published move| of a cue at 15:30 IST on the day (A17)
    rv_session: dict[date, float]  # NIFTY's intraday realised variance of the day (A16b), from 2020
    implied_variance: dict[tuple[str, date], float]  # implied's one-session variance at the day (from its N1 row)
    train_median_ln_vix: float = 0.0
    train_vix_terciles: tuple[float, float] = (0.0, 0.0)
    extra: dict = field(default_factory=dict)


Features = Callable[[Row, Context], list[float] | None]


@dataclass(frozen=True)
class Candidate:
    id: str
    features: Features
    two_band: bool = False  # C2: one scale for 25/75, one for 5/95
    nifty_only: bool = False

    def parameters(self, x: Sequence[float]) -> int:
        return 2 if self.two_band else len(x)

    def bands(self, x: Sequence[float]) -> tuple[Sequence[float], Sequence[float]]:
        return ((1.0, 0.0), (0.0, 1.0)) if self.two_band else (x, x)


def _vix(row: Row, ctx: Context) -> list[float] | None:
    v = ctx.vix.get(row.day)
    return None if v is None else [1.0, math.log(v) - ctx.train_median_ln_vix]


def _vix_change(row: Row, ctx: Context) -> list[float] | None:
    today, before = ctx.vix.get(row.day), ctx.vix.get(ctx.previous_session(row.day))
    return None if today is None or before is None else [1.0, math.log(today / before)]


def _in_horizon(days: frozenset[date], row: Row) -> float:
    return 1.0 if any(row.day < d <= row.target_day for d in days) else 0.0


def _event(row: Row, ctx: Context) -> list[float]:
    """Only events announced before the issue day count (point in time, section 3)."""
    known = frozenset(day for day, announced in ctx.events.items() if announced < row.day)
    return [1.0, _in_horizon(known, row)]


def _expiry(row: Row, ctx: Context) -> list[float] | None:
    days = ctx.expiries.get(row.underlying)
    return None if days is None else [1.0, _in_horizon(days, row)]


def _cues(row: Row, ctx: Context) -> list[float] | None:
    moves = [ctx.cue_move(cue, row.day) for cue in CUES]
    return None if any(m is None for m in moves) else [1.0, *moves]


def _intraday(row: Row, ctx: Context) -> list[float] | None:
    rv, implied = ctx.rv_session.get(row.day), ctx.implied_variance.get((row.underlying, row.day))
    if row.underlying != NIFTY or rv is None or not implied or rv <= 0:
        return None
    return [1.0, math.log(rv / implied)]


def _weekday(row: Row, ctx: Context) -> list[float]:
    weekday = row.target_day.weekday()  # Monday the base; Saturday sessions (special) fall in no dummy
    return [1.0] + [1.0 if weekday == k else 0.0 for k in (1, 2, 3, 4)]


def _regime(row: Row, ctx: Context) -> list[float] | None:
    v = ctx.vix.get(row.day)
    if v is None:
        return None
    low, high = ctx.train_vix_terciles
    return [1.0, 1.0 if low < v <= high else 0.0, 1.0 if v > high else 0.0]


SINGLE: dict[str, Candidate] = {
    "C1": Candidate("C1", lambda row, ctx: [1.0]),
    "C2": Candidate("C2", lambda row, ctx: [1.0], two_band=True),
    "C3": Candidate("C3", _vix),
    "C4": Candidate("C4", _vix_change),
    "C5": Candidate("C5", _event),
    "C6": Candidate("C6", _expiry),
    "C7": Candidate("C7", _cues),
    "C8": Candidate("C8", _intraday, nifty_only=True),
    "C9": Candidate("C9", _weekday),
    "C10": Candidate("C10", _regime),
}


def combined(first: str, second: str) -> Candidate:
    """C11: the intercept plus both chosen conditioners' own columns (section 6)."""

    def features(row: Row, ctx: Context) -> list[float] | None:
        a, b = SINGLE[first].features(row, ctx), SINGLE[second].features(row, ctx)
        return None if a is None or b is None else [1.0, *a[1:], *b[1:]]

    nifty_only = SINGLE[first].nifty_only or SINGLE[second].nifty_only
    return Candidate(f"C11({first}+{second})", features, nifty_only=nifty_only)
