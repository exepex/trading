"""The page's charts (story FL1-1c v2): the timeline (each session's official close against the bands forecast for it,
with today's forecast as the last segment), the trend sparkline and the small range bar of today's card. Each chart
is drawn in its own coordinates (a viewBox) at about its displayed size, so its text stays readable."""

from __future__ import annotations

import math
from collections.abc import Sequence

from .model import Band, Timeline

LEFT, RIGHT, TOP, BOTTOM = 56, 30, 18, 26  # the plot's margins (y labels left, "next" right, x labels below)
SEGMENT = 0.64  # a band segment's share of its session's width
PAD = 0.04


def _nice(step: float) -> float:
    power = 10 ** math.floor(math.log10(step))
    return next(m * power for m in (1, 2, 2.5, 5, 10) if m * power >= step)


class Plot:
    def __init__(self, width: int, height: int, low: float, high: float, slots: int):
        self.width, self.height, self.slots = width, height, slots
        span = (high - low) or abs(high) * 0.01 or 1.0
        self.low, self.high = low - span * PAD, high + span * PAD
        self.inner_w, self.inner_h = width - LEFT - RIGHT, height - TOP - BOTTOM

    def x(self, slot: float) -> float:
        return round(LEFT + (slot + 0.5) * self.inner_w / self.slots, 1)

    def y(self, level: float) -> float:
        return round(TOP + (self.high - level) / (self.high - self.low) * self.inner_h, 1)

    def ticks(self) -> list[float]:
        step = _nice((self.high - self.low) / 4)
        first = math.ceil(self.low / step) * step
        return [first + i * step for i in range(int((self.high - first) / step) + 1)]


def _segment(plot: Plot, slot: int, band: Band, css: str = "") -> str:
    half = plot.inner_w / plot.slots * SEGMENT / 2
    left, width = round(plot.x(slot) - half, 1), round(2 * half, 1)

    def rect(kind: str, low: float, high: float) -> str:
        return (f'<rect class="{kind}{css}" x="{left}" y="{plot.y(high)}" width="{width}" '
                f'height="{round(plot.y(low) - plot.y(high), 1)}"/>')  # fmt: skip

    return rect("b90", band.q05, band.q95) + rect("b50", band.q25, band.q75)


def _marker(x: float, y: float, inside_90: bool, live: bool) -> str:
    if not inside_90:
        return (f'<path class="miss" d="M{x - 4} {y - 4}L{x + 4} {y + 4}M{x - 4} {y + 4}L{x + 4} {y - 4}">'
                "<title>miss: outside the 90% band</title></path>")  # fmt: skip
    return f'<circle class="{"live" if live else "hist"}" cx="{x}" cy="{y}" r="3.2"/>'


def _axes(plot: Plot, labels: Sequence[tuple[int, str]]) -> str:
    out = []
    for tick in plot.ticks():
        y = plot.y(tick)
        out.append(f'<line class="grid" x1="{LEFT}" x2="{plot.width - RIGHT}" y1="{y}" y2="{y}"/>'
                   f'<text class="ylab" x="{LEFT - 6}" y="{y + 4}">{tick:,.0f}</text>')  # fmt: skip
    for slot, text in labels:
        out.append(f'<text class="xlab" x="{plot.x(slot)}" y="{plot.height - 8}">{text}</text>')
    return "".join(out)


def timeline_chart(timeline: Timeline, width: int, height: int, sessions: int, label: str) -> str:
    points, nxt_band = timeline.points[-sessions:], timeline.next_band
    levels = [v for p in points for v in (p.close, p.band.q05, p.band.q95)]
    levels += [nxt_band.q05, nxt_band.q95] if nxt_band else []
    plot = Plot(width, height, min(levels), max(levels), len(points) + 1)
    every = max(1, round(len(points) / 5))
    labels = [(i, f"{p.day.day} {p.day:%b}") for i, p in enumerate(points) if (len(points) - 1 - i) % every == 0]
    bands = "".join(_segment(plot, i, p.band) for i, p in enumerate(points))
    last = len(points)
    nxt = (_segment(plot, last, nxt_band, " next")
           + f'<text class="xlab next" x="{plot.x(last)}" y="{TOP - 3}">next</text>') if nxt_band else ""  # fmt: skip
    path = " ".join(f"{'M' if i == 0 else 'L'}{plot.x(i)} {plot.y(p.close)}" for i, p in enumerate(points))
    marks = "".join(_marker(plot.x(i), plot.y(p.close), p.inside_90, p.live) for i, p in enumerate(points))
    return (f'<svg class="timeline" viewBox="0 0 {width} {height}" role="img" aria-label="{label}">'
            f'{_axes(plot, labels)}{bands}{nxt}<path class="close" d="{path}"/>{marks}</svg>')  # fmt: skip


def sparkline(values: Sequence[float | None], width: int = 120, height: int = 30) -> str:
    """The 90% band's trailing coverage: a line, the 90% aim dashed and the 80% floor dotted."""

    def y(v: float) -> float:
        return round(2 + (1 - (v - 0.5) / 0.5) * (height - 4), 1)

    known = [(i, v) for i, v in enumerate(values) if v is not None]
    step = width / max(len(values) - 1, 1)
    path = " ".join(f"{'M' if n == 0 else 'L'}{round(i * step, 1)} {y(min(max(v, 0.5), 1.0))}"
                    for n, (i, v) in enumerate(known))  # fmt: skip
    return (f'<svg class="spark" viewBox="0 0 {width} {height}" role="img" aria-label="90% band coverage trend">'
            f'<line class="aim" x1="0" x2="{width}" y1="{y(0.9)}" y2="{y(0.9)}"/>'
            f'<line class="floor" x1="0" x2="{width}" y1="{y(0.8)}" y2="{y(0.8)}"/>'
            f'<path class="trend" d="{path}"/></svg>')  # fmt: skip


def range_bar(band: Band, price: float, low: float, high: float) -> str:
    """Today's card: one range on a scale shared by the card's rows, today's price as a tick."""

    def x(level: float) -> float:
        return round(100 * (level - low) / ((high - low) or 1.0), 2)

    return (f'<svg class="rbar" role="img" aria-label="range">'
            f'<rect class="b90" x="{x(band.q05)}%" y="2" width="{x(band.q95) - x(band.q05)}%" height="12" rx="2"/>'
            f'<rect class="b50" x="{x(band.q25)}%" y="2" width="{x(band.q75) - x(band.q25)}%" height="12" rx="2"/>'
            f'<line class="now" x1="{x(price)}%" x2="{x(price)}%" y1="0" y2="16"/></svg>')  # fmt: skip
