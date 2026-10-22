"""Fakes for the signed-off design's tests (story FL1-1d, design part): a page with 30 scored sessions, misses, a
method record with its rolling trend, and both editions. Made-up levels only, never market data."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from fno.forecast_lab.page.model import (
    Band,
    Cell,
    Horizon,
    IndexView,
    MethodRecord,
    Miss,
    PageView,
    RangeView,
    Timeline,
    Window,
)

from .page_builders import BAND, DAY, days, outcome

NIFTY_BAND = Band(21850.0, 22100.0, 22240.0, 22380.0, 22530.0)
# 30 closes around a made-up level: inside the 50% range, inside the 90% only, and outside (a miss), in turn
CLOSES = [22240 + ((i * 97) % 500 - 250) for i in range(30)]
MISS_DAYS = (3, 17, 27)  # positions whose close is pushed outside "almost certainly"


def band_at(i: int) -> Band:
    shift = (i * 31) % 200 - 100
    return Band(*(q + shift for q in (NIFTY_BAND.q05, NIFTY_BAND.q25, NIFTY_BAND.q50, NIFTY_BAND.q75, NIFTY_BAND.q95)))


def sessions(n: int = 30):
    return days(n, DAY)


def outcomes(n: int = 30):
    points = []
    for i, day in enumerate(sessions(n)):
        band = band_at(i)
        close = float(CLOSES[i] + (band.q50 - NIFTY_BAND.q50))
        if i in MISS_DAYS:
            close = band.q95 + 60 if i % 2 else band.q05 - 60
        points.append(outcome(day, close, band))
    return tuple(points)


def method(points, best: bool = True) -> MethodRecord:
    cells = tuple(Cell(p.day, p.inside_50, p.inside_90, p.live) for p in points)
    rolling = tuple(None if i < 19 else sum(p.inside_90 for p in points[i - 19 : i + 1]) / 20
                    for i in range(len(points)))  # fmt: skip
    windows = (Window(7, 7, 0.4, 0.9, 100.0), Window(14, 14, 0.4, 0.86, 100.0), Window(30, 30, 0.4, 0.9, 100.0))
    return MethodRecord("implied", cells, windows, rolling, best)


def nifty(n: int = 30, edition_fields: bool = False) -> IndexView:
    points = outcomes(n)
    misses = tuple(Miss(points[i].day, "above" if i % 2 else "below", 60.0, ("a made-up reason",)) for i in MISS_DAYS)
    today = (RangeView("N1", DAY + timedelta(days=1), NIFTY_BAND, 0.5, "tomorrow"),
             RangeView("N3", DAY + timedelta(days=3), Band(21700.0, 22000.0, 22250.0, 22500.0, 22800.0), 0.5,
                       "in 3 trading days, Mon 26 Oct"))  # fmt: skip
    right = sum(p.inside_90 for p in points)
    horizons = (Horizon(Timeline("N1", "implied", points), (method(points),)),)
    return IndexView("NIFTY", float(points[-1].close), "close", "implied", today, False, 0, 60, horizons, right, n,
                     misses, "green" if right >= 25 else "amber", "Good" if right >= 25 else "Watch",
                     tuple(points[i].day for i in reversed(MISS_DAYS)))  # fmt: skip


def scaled(band: Band, scale: float) -> Band:
    return Band(*(q * scale for q in (band.q05, band.q25, band.q50, band.q75, band.q95)))


def banknifty() -> IndexView:
    index, scale = nifty(), 2.5
    points = tuple(replace(p, close=p.close * scale, band=scaled(p.band, scale))
                   for p in index.horizons[0].timeline.points)  # fmt: skip
    today = tuple(replace(r, band=scaled(r.band, scale)) for r in index.today)
    return replace(index, underlying="BANKNIFTY", price=points[-1].close, today=today,
                   horizons=(Horizon(Timeline("N1", "implied", points), (method(points),)),))  # fmt: skip


def page(edition: str = "evening", indices=None) -> PageView:
    view = PageView(DAY, "Live, sealed", tuple(indices or (nifty(), banknifty())), ())
    try:
        return replace(view, edition=edition)
    except TypeError:  # the model before FL1-1d-1: no edition field, the renderer draws the evening
        return view


__all__ = ["BAND", "page", "nifty", "banknifty", "outcomes", "sessions"]
