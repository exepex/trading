"""One chart per index: a column per trading day (its forecast range as two shaded blocks, the close as a dot),
then the forecast columns on the right with their numbers written beside them. Standard library only."""

import math
from dataclasses import dataclass


def fmt(value):
    return f"{int(round(value)):,}"


def fmt_low(value):
    """A range's lower edge rounded down to 10 (the builder's rule in fno/forecast_lab/page/plain.py: outward)."""
    return f"{int(math.floor(value / 10) * 10):,}"


def fmt_high(value):
    """A range's upper edge rounded up to 10 (outward, as above)."""
    return f"{int(math.ceil(value / 10) * 10):,}"


def fmt_mid(value):
    """The middle guess rounded to the nearest 10."""
    return f"{int(round(value / 10) * 10):,}"


@dataclass(frozen=True)
class Layout:
    width: int
    plot_height: int = 230
    top: int = 40
    axis_width: int = 54
    column_width: int = 22
    forecast_slot: int = 92
    bottom: int = 52


def _nice_step(span):
    for step in (100, 200, 250, 500, 1000, 2000):
        if span / step <= 4.5:
            return step
    return 5000


def _axis_values(low, high):
    step = _nice_step(high - low)
    first = (int(low) // step + 1) * step
    return [v for v in range(first, int(high) + 1, step)], step


class RangeColumnChart:
    """Draws the SVG. `days` are the past sessions to show; `forecasts` the (label, range) pairs on the right."""

    def __init__(self, days, forecasts, layout, label_every=1):
        self.days, self.forecasts, self.layout, self.label_every = days, forecasts, layout, label_every
        values = [d["lo90"] for d in days] + [d["hi90"] for d in days] + [d["close"] for d in days]
        values += [f["lo90"] for _, f in forecasts] + [f["hi90"] for _, f in forecasts]
        pad = (max(values) - min(values)) * 0.06
        self.low, self.high = min(values) - pad, max(values) + pad
        self.plot_left = layout.axis_width
        self.plot_right = layout.width - layout.forecast_slot * len(forecasts) - 8
        self.height = layout.top + layout.plot_height + layout.bottom

    def y(self, value):
        lay = self.layout
        return lay.top + lay.plot_height * (self.high - value) / (self.high - self.low)

    def x(self, i):
        slot = (self.plot_right - self.plot_left) / len(self.days)
        return self.plot_left + slot * (i + 0.5)

    def _grid(self):
        values, _ = _axis_values(self.low, self.high)
        right = self.layout.width - 8
        out = []
        for v in values:
            y = self.y(v)
            out.append(f'<line class="grid" x1="{self.plot_left}" x2="{right}" y1="{y:.1f}" y2="{y:.1f}"/>')
            out.append(f'<text class="ax" x="{self.plot_left - 8}" y="{y + 4:.1f}">{fmt(v)}</text>')
        return out

    def _column(self, i, d):
        w = self.layout.column_width
        x = self.x(i) - w / 2
        cls = "ok" if d["right"] else "miss"
        word = "inside" if d["right"] else "outside"
        tip = (f'{d["date"]}: almost certainly {fmt(d["lo90"])}–{fmt(d["hi90"])}, most likely '
               f'{fmt(d["lo50"])}–{fmt(d["hi50"])}, closed {fmt(d["close"])} ({word})')
        parts = [
            f"<g><title>{tip}</title>",
            f'<rect class="r90" x="{x:.1f}" y="{self.y(d["hi90"]):.1f}" width="{w}" '
            f'height="{self.y(d["lo90"]) - self.y(d["hi90"]):.1f}" rx="3"/>',
            f'<rect class="r50" x="{x:.1f}" y="{self.y(d["hi50"]):.1f}" width="{w}" '
            f'height="{self.y(d["lo50"]) - self.y(d["hi50"]):.1f}" rx="2"/>',
            f'<circle class="close {cls}" cx="{self.x(i):.1f}" cy="{self.y(d["close"]):.1f}" r="5.5"/>',
            "</g>",
        ]
        if i % self.label_every == 0:
            day, month = d["date"].split()
            base = self.layout.top + self.layout.plot_height
            parts.append(f'<text class="day" x="{self.x(i):.1f}" y="{base + 18}">{day}</text>')
            parts.append(f'<text class="mon" x="{self.x(i):.1f}" y="{base + 31}">{month}</text>')
            mark = "&#10003;" if d["right"] else "&#10007;"
            parts.append(f'<text class="mark {cls}" x="{self.x(i):.1f}" y="{base + 48}">{mark}</text>')
        return parts

    def _forecast(self, k, label, f):
        lay = self.layout
        left = self.plot_right + lay.forecast_slot * k
        cx = left + 20
        w = lay.column_width
        x = cx - w / 2
        tx = cx + w / 2 + 6
        parts = [
            f'<text class="fh" x="{cx - w / 2:.0f}" y="{lay.top - 22}">{label}</text>',
            f'<text class="fh2" x="{cx - w / 2:.0f}" y="{lay.top - 8}">{f["date"]}</text>',
            f'<rect class="r90" x="{x:.1f}" y="{self.y(f["hi90"]):.1f}" width="{w}" '
            f'height="{self.y(f["lo90"]) - self.y(f["hi90"]):.1f}" rx="3"/>',
            f'<rect class="r50" x="{x:.1f}" y="{self.y(f["hi50"]):.1f}" width="{w}" '
            f'height="{self.y(f["lo50"]) - self.y(f["hi50"]):.1f}" rx="2"/>',
            f'<line class="mid" x1="{x - 3:.1f}" x2="{x + w + 3:.1f}" '
            f'y1="{self.y(f["mid"]):.1f}" y2="{self.y(f["mid"]):.1f}"/>',
        ]
        labels = [("hi90", "faint", fmt_high), ("hi50", "num", fmt_high), ("mid", "centre", fmt_mid),
                  ("lo50", "num", fmt_low), ("lo90", "faint", fmt_low)]
        ys = _spread([self.y(f[key]) for key, _, _ in labels], 17)
        for (key, cls, show), y in zip(labels, ys):
            parts.append(f'<text class="{cls}" x="{tx:.0f}" y="{y + 4.5:.1f}">{show(f[key])}</text>')
        return parts

    def svg(self, aria):
        lay = self.layout
        sep = self.plot_right
        body = self._grid()
        body.append(f'<rect class="future" x="{sep}" y="{lay.top - 30}" width="{lay.width - sep}" '
                    f'height="{lay.plot_height + 30}" rx="4"/>')
        for i, d in enumerate(self.days):
            body += self._column(i, d)
        for k, (label, f) in enumerate(self.forecasts):
            body += self._forecast(k, label, f)
        return (f'<svg class="chart" viewBox="0 0 {lay.width} {self.height}" role="img" aria-label="{aria}">'
                + "".join(body) + "</svg>")


def _spread(ys, gap):
    """Pushes labels apart so none overlap, keeping their order (a one-pass nudge from the top)."""
    out = []
    for y in ys:
        if out and y - out[-1] < gap:
            y = out[-1] + gap
        out.append(y)
    return out
