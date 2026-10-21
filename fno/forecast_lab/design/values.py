"""The plain values the charts and blocks draw, read from the `PageView` once. A `Day` is one scored session with
its forecast band and its result; a `Range` is one of today's forecasts. The only arithmetic here is the gap
(close minus the forecast middle) and its percentage, until the builder's model carries them (FL1-1d-2)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..page.model import Band, IndexView, Outcome, PageView, RangeView
from .formats import long, short, status


@dataclass(frozen=True)
class Day:
    day: date
    close: float
    lo90: float
    lo50: float
    mid: float
    hi50: float
    hi90: float
    result: str  # "green", "amber" or "red"
    live: bool
    provisional: bool

    @property
    def date(self) -> str:
        return short(self.day)

    @property
    def date_long(self) -> str:
        return long(self.day)

    @property
    def gap(self) -> float:
        return self.close - self.mid

    @property
    def gap_pct(self) -> float:
        return self.gap / self.mid * 100


@dataclass(frozen=True)
class Range:
    day: date
    when: str
    lo90: float
    lo50: float
    mid: float
    hi50: float
    hi90: float

    @property
    def date(self) -> str:
        return long(self.day)


def _edges(band: Band) -> tuple[float, float, float, float, float]:
    return band.q05, band.q25, band.q50, band.q75, band.q95


def day_of(point: Outcome) -> Day:
    return Day(point.day, point.close, *_edges(point.band), status(point), point.live,
               bool(getattr(point, "provisional", False)))  # fmt: skip


def range_of(view: RangeView) -> Range:
    return Range(view.target_day, view.when, *_edges(view.band))


def days_of(index: IndexView, last: int) -> list[Day]:
    """The last `last` scored sessions of the next-session timeline, oldest first."""
    points = index.horizons[0].timeline.points if index.horizons else ()
    return [day_of(p) for p in points[-last:]]


def today_of(index: IndexView, horizon: str) -> Range | None:
    return next((range_of(r) for r in index.today if r.horizon == horizon), None)


def rolling_90(index: IndexView) -> list[float | None]:
    """The shown method's rolling 20-session share inside the 90% range, per grid session."""
    if not index.horizons:
        return []
    return next((list(m.rolling_90) for m in index.horizons[0].methods if m.best), [])


def reason_for(index: IndexView, day: Day) -> str:
    return next(("; ".join(m.reasons) for m in index.misses if m.day == day.day), "")


def edition_of(view: PageView) -> str:
    return getattr(view, "edition", "evening")
