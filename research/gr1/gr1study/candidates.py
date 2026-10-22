"""GR1's candidates C1-C11 (protocol section 6). Each turns a row into its conditioner vector `x` (intercept first),
or None when an input is missing that day (the day is dropped for that candidate, and reported; section 7). Every
input is the one known at the issue time (section 3); `Context` holds them, built by `inputs.py` from real data or by
the tests from synthetic data."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
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
    expiries: dict[str, dict[date, frozenset[date]]]  # each index's option expiries listed in d's own file (SF2)
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
    train_from: date | None = None  # C8: its data starts 2 Jan 2020, so its train period does (section 7)
    needs: str = ""  # the input a dropped day lacks (judge 442 note 3)
    scales: tuple[float, ...] = ()  # train SD of each non-intercept column (judge 442 SF1); empty: raw units

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
    """The expiries listed in d's own F&O file only: a later revision never counts (judge 442 SF2)."""
    listed = ctx.expiries.get(row.underlying, {}).get(row.day)
    return None if listed is None else [1.0, _in_horizon(listed, row)]


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
    "C3": Candidate("C3", _vix, needs="India VIX of d"),
    "C4": Candidate("C4", _vix_change, needs="India VIX of d or of the session before"),
    "C5": Candidate("C5", _event),
    "C6": Candidate("C6", _expiry, needs="d's F&O file (its expiry list)"),
    "C7": Candidate("C7", _cues, needs="a global cue by A17's rule (none usable, or older than its age limit)"),
    "C8": Candidate(
        "C8",
        _intraday,
        nifty_only=True,
        train_from=date(2020, 1, 2),
        needs="NIFTY's intraday realised variance of d, or implied's N1 variance",
    ),
    "C9": Candidate("C9", _weekday),
    "C10": Candidate("C10", _regime, needs="India VIX of d"),
}


def column_scales(data: Sequence[tuple[Row, Sequence[float]]]) -> tuple[float, ...]:
    """The SD of each non-intercept column over the given (train) rows; a constant column keeps 1 (judge 442 SF1)."""
    if not data or len(data[0][1]) <= 1:
        return ()
    found = []
    for j in range(1, len(data[0][1])):
        values = [x[j] for _, x in data]
        mean = sum(values) / len(values)
        sd = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
        found.append(sd if sd > 0 else 1.0)
    return tuple(found)


def standardised(candidate: Candidate, scales: Sequence[float]) -> Candidate:
    """The same candidate with each non-intercept column divided by its train SD, so `theta`'s bound means the same
    for every conditioner. Run 2 rebuilds it from the SDs stored in `selection.json`."""
    if not scales:
        return candidate
    raw = candidate.features

    def features(row: Row, ctx: Context) -> list[float] | None:
        x = raw(row, ctx)
        return None if x is None else [x[0], *(v / s for v, s in zip(x[1:], scales, strict=True))]

    return replace(candidate, features=features, scales=tuple(scales))


def combined(first: str, second: str) -> Candidate:
    """C11: the intercept plus both chosen conditioners' own columns (section 6)."""

    def features(row: Row, ctx: Context) -> list[float] | None:
        a, b = SINGLE[first].features(row, ctx), SINGLE[second].features(row, ctx)
        return None if a is None or b is None else [1.0, *a[1:], *b[1:]]

    nifty_only = SINGLE[first].nifty_only or SINGLE[second].nifty_only
    starts = [d for d in (SINGLE[first].train_from, SINGLE[second].train_from) if d]
    needs = " / ".join(n for n in (SINGLE[first].needs, SINGLE[second].needs) if n)
    return Candidate(f"C11({first}+{second})", features, nifty_only=nifty_only, train_from=max(starts, default=None),
                     needs=needs)  # fmt: skip
