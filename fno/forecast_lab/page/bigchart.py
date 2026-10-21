"""The report's main graph (story FL1-1c v4): for each recent session, the "most likely" range as a shaded ribbon, its
middle as a thin line and "almost certainly" as a faint outer ribbon, all as forecast the session before; the actual
close as a line with a green tick (inside "almost certainly") or a red cross (outside) on each close. At the right
edge, the next trading day's and the 3-day forecasts, each labelled with its upper, middle and lower numbers."""

from __future__ import annotations

import math
from collections.abc import Sequence

from .model import Band, Outcome, RangeView
from .plain import day_short, outward

LEFT, TOP, BOTTOM = 58, 16, 30
FORECAST_SPACE = 190  # the right-hand space for the two forecasts and their numbers
TICK_STEPS = (50, 100, 200, 250, 500, 1000, 2000)
MAX_TICKS = 16


class Frame:
    def __init__(self, width: int, height: int, sessions: int, low: float, high: float):
        self.width, self.height = width, height
        self.plot_w = width - LEFT - FORECAST_SPACE
        self.step = self.plot_w / max(sessions, 1)
        pad = (high - low) * 0.04 or 1.0
        self.low, self.high = low - pad, high + pad

    def x(self, i: float) -> float:
        return round(LEFT + (i + 0.5) * self.step, 1)

    def y(self, level: float) -> float:
        return round(TOP + (self.high - level) / (self.high - self.low) * (self.height - TOP - BOTTOM), 1)

    def ticks(self) -> list[int]:
        step = next((s for s in TICK_STEPS if (self.high - self.low) / s <= MAX_TICKS), TICK_STEPS[-1])
        first = math.ceil(self.low / step) * step
        return list(range(first, int(self.high) + 1, step))


def _ribbon(frame: Frame, points: Sequence[Outcome], upper: str, lower: str, css: str) -> str:
    top = [f"{frame.x(i)},{frame.y(getattr(p.band, upper))}" for i, p in enumerate(points)]
    bottom = [f"{frame.x(i)},{frame.y(getattr(p.band, lower))}" for i, p in reversed(list(enumerate(points)))]
    return f'<polygon class="{css}" points="{" ".join(top + bottom)}"/>'


def _marks(frame: Frame, points: Sequence[Outcome]) -> str:
    out = []
    for i, p in enumerate(points):
        x, y = frame.x(i), frame.y(p.close)
        word = "inside" if p.inside_90 else "outside"
        glyph, css = ("&#10003;", "hit") if p.inside_90 else ("&#10007;", "miss")
        out.append(f'<text class="{css}" x="{x}" y="{y + 4.5}"><title>{day_short(p.day)}: close {p.close:,.0f}, '
                   f'{word} &#8220;almost certainly&#8221;</title>{glyph}</text>')  # fmt: skip
    return "".join(out)


def _axes(frame: Frame, points: Sequence[Outcome]) -> str:
    out = []
    for tick in frame.ticks():
        y = frame.y(tick)
        out.append(f'<line class="grid" x1="{LEFT}" x2="{frame.width - 8}" y1="{y}" y2="{y}"/>'
                   f'<text class="ylab" x="{LEFT - 6}" y="{y + 4}">{tick:,}</text>')  # fmt: skip
    every = max(1, round(len(points) / 6))
    for i, p in enumerate(points):
        if (len(points) - 1 - i) % every == 0:
            out.append(f'<text class="xlab" x="{frame.x(i)}" y="{frame.height - 10}">{p.day.day} {p.day:%b}</text>')
    return "".join(out)


def _bar(frame: Frame, x: float, low: float, high: float, css: str) -> str:
    return f'<rect class="{css}" x="{x - 7}" y="{frame.y(high)}" width="14" height="{frame.y(low) - frame.y(high)}"/>'


def _forecast(frame: Frame, x: float, view: RangeView, title: str) -> str:
    b: Band = view.band
    likely_low, likely_high = outward(b.q25, b.q75)
    sure_low, sure_high = outward(b.q05, b.q95)
    labels = ((likely_high, b.q75, "num"), (round(b.q50, -1), b.q50, "num centre"), (likely_low, b.q25, "num"),
              (sure_high, b.q95, "num faint"), (sure_low, b.q05, "num faint"))  # fmt: skip
    text = "".join(f'<text class="{css}" x="{x + 13}" y="{frame.y(at) + 4}">{value:,.0f}</text>'
                   for value, at, css in labels)  # fmt: skip
    return (f"{_bar(frame, x, b.q05, b.q95, 'fc90')}{_bar(frame, x, b.q25, b.q75, 'fc50')}"
            f'<line class="fcmid" x1="{x - 9}" x2="{x + 9}" y1="{frame.y(b.q50)}" y2="{frame.y(b.q50)}"/>'
            f'<text class="fclab" x="{x}" y="{TOP - 4}">{title}</text>{text}')  # fmt: skip


def big_chart(points: Sequence[Outcome], forecasts: Sequence[RangeView], width: int, height: int,
              label: str, chart_id: str = "") -> str:  # fmt: skip
    levels = [v for p in points for v in (p.close, p.band.q05, p.band.q95)]
    levels += [v for f in forecasts for v in (f.band.q05, f.band.q95)]
    frame = Frame(width, height, len(points), min(levels), max(levels))
    middle = " ".join(f"{frame.x(i)},{frame.y(p.band.q50)}" for i, p in enumerate(points))
    close = " ".join(f"{frame.x(i)},{frame.y(p.close)}" for i, p in enumerate(points))
    first_x = width - FORECAST_SPACE + 22
    fc = "".join(_forecast(frame, first_x + n * 92, f, f"forecast {f.target_day.day} {f.target_day:%b}")
                 for n, f in enumerate(forecasts))  # fmt: skip
    ident = f' id="{chart_id}"' if chart_id else ""
    return (f'<svg{ident} class="big" viewBox="0 0 {width} {height}" role="img" aria-label="{label}">'
            f"{_axes(frame, points)}{_ribbon(frame, points, 'q95', 'q05', 'r90')}"
            f"{_ribbon(frame, points, 'q75', 'q25', 'r50')}<polyline class=\"mid\" points=\"{middle}\"/>"
            f'<polyline class="close" points="{close}"/>{_marks(frame, points)}'
            f'<line class="sep" x1="{width - FORECAST_SPACE + 4}" x2="{width - FORECAST_SPACE + 4}" y1="{TOP}" '
            f'y2="{height - BOTTOM}"/>{fc}</svg>')  # fmt: skip
