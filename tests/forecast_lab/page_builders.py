"""Fakes for story FL1-1c's page: hand-made bands, outcomes and score points (made-up numbers, not market data)."""

from __future__ import annotations

from datetime import date, timedelta

from fno.forecast_lab.page.history import ScorePoint
from fno.forecast_lab.page.model import Band, IndexView, Outcome, PageView, RangeView

DAY = date(2026, 10, 23)
BAND = Band(980.0, 995.0, 1000.0, 1005.0, 1020.0)


def outcome(day: date, close: float, band: Band = BAND) -> Outcome:
    return Outcome(day, close, band, band.q25 <= close <= band.q75, band.q05 <= close <= band.q95, False)


def days(n: int, last: date = DAY) -> list[date]:
    out, current = [], last
    while len(out) < n:
        if current.weekday() < 5:
            out.append(current)
        current -= timedelta(days=1)
    return out[::-1]


def point(method: str, target: date, close: float = 1000.0, horizon: str = "N1", error: float = 5.0,
          inside=(True, True), live: bool = False) -> ScorePoint:  # fmt: skip
    return ScorePoint(method, horizon, target, close, error, inside[0], inside[1], live, None, BAND)


def index(right: int = 26, scored: int = 30, today=None) -> IndexView:
    ranges = today if today is not None else (RangeView("N1", DAY + timedelta(days=3), BAND, 0.5),)
    return IndexView("NIFTY", 1001.0, "3 pm price", "implied", ranges, False, 0, 60, (), right, scored)


def page(indices=None, system=()) -> PageView:
    return PageView(DAY, "Live, sealed", tuple(indices or (index(),)), (), tuple(system))
