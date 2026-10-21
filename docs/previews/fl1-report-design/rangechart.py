"""Graph 1 and 2: one forecast range on a horizontal scale with gridlines, every edge written as a number, and a
marker for a price (yesterday's close in the morning, the actual close in the evening). Standard library only."""

import math
from dataclasses import dataclass

from linechart import fmt, fmt_high, fmt_low, fmt_mid


@dataclass(frozen=True)
class RangeLayout:
    width: int
    grid_step: int  # a hairline every step (50 for NIFTY, 100 for BANKNIFTY)
    label_step: int  # an axis number every label_step
    left: int = 16
    right: int = 16


class RangeRow:
    """One row: a band (lo90, lo50, mid, hi50, hi90), a title, and an optional marker (value, css class, word)."""

    def __init__(self, title, band, marker=None, small=False):
        self.title, self.band, self.marker, self.small = title, band, marker, small


class HorizontalRangeChart:
    def __init__(self, rows, layout):
        self.rows, self.lay = rows, layout
        values = [v for r in rows for v in (r.band["lo90"], r.band["hi90"])]
        values += [r.marker[0] for r in rows if r.marker]
        step = layout.grid_step
        self.low = math.floor((min(values) - step) / step) * step
        self.high = math.ceil((max(values) + step) / step) * step
        self.row_h = [56 if r.small else 90 for r in rows]
        self.height = 14 + sum(self.row_h) + 26
        px_per_point = (layout.width - layout.left - layout.right) / (self.high - self.low)
        self.label_step = layout.label_step
        while self.label_step * px_per_point < 72:
            self.label_step += layout.label_step

    def x(self, value):
        lay = self.lay
        return lay.left + (lay.width - lay.left - lay.right) * (value - self.low) / (self.high - self.low)

    def _grid(self):
        out, top, bottom = [], 10, self.height - 24
        for v in range(int(self.low), int(self.high) + 1, self.lay.grid_step):
            x = self.x(v)
            major = v % self.label_step == 0
            out.append(f'<line class="grid{" major" if major else ""}" x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{bottom}"/>')
            if major:
                out.append(f'<text class="ax" x="{x:.1f}" y="{bottom + 15}">{fmt(v)}</text>')
        return out

    def _row(self, r, y):
        b, h = r.band, (14 if r.small else 22)
        cy = y + (36 if not r.small else 28)
        size = "s" if r.small else ""
        parts = [f'<text class="title" x="{self.lay.left}" y="{y + 11}">{r.title}</text>',
                 f'<rect class="r90" x="{self.x(b["lo90"]):.1f}" y="{cy - h / 2:.1f}" '
                 f'width="{self.x(b["hi90"]) - self.x(b["lo90"]):.1f}" height="{h}" rx="3"/>',
                 f'<rect class="r50" x="{self.x(b["lo50"]):.1f}" y="{cy - h / 2:.1f}" '
                 f'width="{self.x(b["hi50"]) - self.x(b["lo50"]):.1f}" height="{h}" rx="2"/>',
                 f'<line class="mid" x1="{self.x(b["mid"]):.1f}" x2="{self.x(b["mid"]):.1f}" '
                 f'y1="{cy - h / 2 - 3:.1f}" y2="{cy + h / 2 + 3:.1f}"/>']
        above = cy - h / 2 - 5
        below = cy + h / 2 + 13
        parts += [f'<text class="v50 {size}" text-anchor="end" x="{self.x(b["lo50"]) - 3:.1f}" y="{above:.1f}">{fmt_low(b["lo50"])}</text>',
                  f'<text class="v50 {size}" text-anchor="start" x="{self.x(b["hi50"]) + 3:.1f}" y="{above:.1f}">{fmt_high(b["hi50"])}</text>',
                  f'<text class="vmid {size}" x="{self.x(b["mid"]):.1f}" y="{above:.1f}">{fmt_mid(b["mid"])}</text>',
                  f'<text class="v90 {size}" text-anchor="end" x="{self.x(b["lo90"]) - 3:.1f}" y="{below:.1f}">{fmt_low(b["lo90"])}</text>',
                  f'<text class="v90 {size}" text-anchor="start" x="{self.x(b["hi90"]) + 3:.1f}" y="{below:.1f}">{fmt_high(b["hi90"])}</text>']
        if r.marker:
            value, cls, word = r.marker
            mx = self.x(value)
            parts.append(f'<line class="marker {cls}" x1="{mx:.1f}" x2="{mx:.1f}" y1="{cy - h / 2 - 6:.1f}" y2="{below + 4:.1f}"/>')
            parts.append(f'<circle class="markdot {cls}" cx="{mx:.1f}" cy="{cy:.1f}" r="5"/>')
            anchor, dx = "middle", 0
            if mx - self.x(b["lo90"]) < 70:
                anchor, dx = "start", -4
            elif self.x(b["hi90"]) - mx < 70:
                anchor, dx = "end", 4
            parts.append(f'<text class="mark {cls}" text-anchor="{anchor}" x="{mx + dx:.1f}" y="{below + 16:.1f}">'
                         f'{word} {fmt(value)}</text>')
        return parts

    def svg(self, aria):
        body = self._grid()
        y = 14
        for r, h in zip(self.rows, self.row_h):
            body += self._row(r, y)
            y += h
        return (f'<svg class="range" viewBox="0 0 {self.lay.width} {self.height}" role="img" aria-label="{aria}">'
                + "".join(body) + "</svg>")
