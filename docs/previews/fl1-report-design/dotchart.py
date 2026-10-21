"""Graph 3: the last sessions, one column per day: the forecast range as a pale bar ("almost certainly") with a
darker block ("most likely"), a dot where the index closed, coloured by the result, the close written beside it,
and the forecast high, close and low in three rows under the dates. Standard library only."""

import math
from dataclasses import dataclass

from linechart import fmt, status


@dataclass(frozen=True)
class DotLayout:
    width: int
    grid_step: int
    label_step: int
    plot_height: int = 220
    top: int = 16
    axis_width: int = 48
    bottom: int = 86


class DotRangeChart:
    def __init__(self, days, layout):
        self.days, self.lay = days, layout
        values = [v for d in days for v in (d["lo90"], d["hi90"], d["close"])]
        step = layout.grid_step
        self.low = math.floor((min(values) - step * 0.5) / step) * step
        self.high = math.ceil((max(values) + step * 0.5) / step) * step
        self.slot = (layout.width - layout.axis_width - 12) / len(days)
        self.height = layout.top + layout.plot_height + layout.bottom

    def y(self, value):
        return self.lay.top + self.lay.plot_height * (self.high - value) / (self.high - self.low)

    def x(self, i):
        return self.lay.axis_width + 12 + self.slot * (i + 0.5)

    def _grid(self):
        out = []
        for v in range(int(self.low), int(self.high) + 1, self.lay.grid_step):
            y = self.y(v)
            major = v % self.lay.label_step == 0
            out.append(f'<line class="grid{" major" if major else ""}" x1="{self.lay.axis_width}" '
                       f'x2="{self.lay.width - 6}" y1="{y:.1f}" y2="{y:.1f}"/>')
            if major:
                out.append(f'<text class="ax" x="{self.lay.axis_width - 8}" y="{y + 4:.1f}">{fmt(v)}</text>')
        return out

    def _sides(self):
        """The close label sits right of its dot, left on the last day, and left when the next day's label
        would sit on top of it."""
        ys = [self.y(d["close"]) for d in self.days]
        sides = ["right"] * len(ys)
        sides[-1] = "left"
        for i in range(len(ys) - 2, -1, -1):
            if sides[i + 1] == "left" and abs(ys[i] - ys[i + 1]) < 13:
                sides[i] = "left"
        return sides

    def _column(self, i, d, side):
        x, st, w = self.x(i), status(d), 12
        yc = self.y(d["close"])
        anchor, dx = ("end", -9) if side == "left" else ("start", 9)
        base = self.lay.top + self.lay.plot_height
        day, month = d["date"].split()
        return [
            f'<rect class="r90" x="{x - w / 2:.1f}" y="{self.y(d["hi90"]):.1f}" width="{w}" '
            f'height="{self.y(d["lo90"]) - self.y(d["hi90"]):.1f}" rx="3"/>',
            f'<rect class="r50" x="{x - w / 2:.1f}" y="{self.y(d["hi50"]):.1f}" width="{w}" '
            f'height="{self.y(d["lo50"]) - self.y(d["hi50"]):.1f}" rx="2"/>',
            f'<circle class="dot {st}" cx="{x:.1f}" cy="{yc:.1f}" r="5.5"/>',
            f'<text class="v close" text-anchor="{anchor}" x="{x + dx:.1f}" y="{yc + 4:.1f}">{fmt(d["close"])}</text>',
            f'<text class="day" x="{x:.1f}" y="{base + 18}">{day}</text>',
            f'<text class="mon" x="{x:.1f}" y="{base + 30}">{month}</text>',
            f'<text class="s" x="{x:.1f}" y="{base + 50}">{fmt(d["hi50"])}</text>',
            f'<text class="s close {st}" x="{x:.1f}" y="{base + 65}">{fmt(d["close"])}</text>',
            f'<text class="s" x="{x:.1f}" y="{base + 80}">{fmt(d["lo50"])}</text>',
        ]

    def svg(self, aria):
        base = self.lay.top + self.lay.plot_height
        body = self._grid()
        for i, (d, side) in enumerate(zip(self.days, self._sides())):
            body += self._column(i, d, side)
        for word, dy in (("high", 50), ("close", 65), ("low", 80)):
            body.append(f'<text class="sl" x="{self.lay.axis_width - 6}" y="{base + dy}">{word}</text>')
        return (f'<svg class="dots" viewBox="0 0 {self.lay.width} {self.height}" role="img" aria-label="{aria}">'
                + "".join(body) + "</svg>")
