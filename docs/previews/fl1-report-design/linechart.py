"""The v6 chart: three lines per index (the forecast high and low of "most likely", and the actual close), every
point labelled with its value, the close marker coloured by the day's result, and the next-day forecast continuing
the lines into a shaded forecast zone. Standard library only."""

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
    return f"{int(round(value / 10) * 10):,}"


def status(day):
    """GREEN inside "most likely", AMBER inside "almost certainly" only, RED outside both (owner, v6 brief)."""
    if day["lo50"] <= day["close"] <= day["hi50"]:
        return "green"
    if day["lo90"] <= day["close"] <= day["hi90"]:
        return "amber"
    return "red"


@dataclass(frozen=True)
class Layout:
    width: int
    grid_step: int
    plot_height: int = 300
    top: int = 34
    axis_width: int = 48
    zone_width: int = 122
    bottom: int = 88  # two-line dates and the three value rows (high, close, low)
    label_min_slot: int = 44  # label every close only when a day has at least this many px


class ForecastLineChart:
    def __init__(self, days, forecast, layout):
        self.days, self.forecast, self.lay = days, forecast, layout
        values = [v for d in days for v in (d["lo50"], d["hi50"], d["close"])]
        values += [forecast["lo50"], forecast["hi50"], forecast["mid"]]
        step = layout.grid_step
        self.low = math.floor((min(values) - step * 0.6) / step) * step
        self.high = math.ceil((max(values) + step * 0.6) / step) * step
        self.plot_left = layout.axis_width
        self.zone_left = layout.width - layout.zone_width
        self.slot = (self.zone_left - self.plot_left - 16) / len(days)
        self.height = layout.top + layout.plot_height + layout.bottom

    def y(self, value):
        return self.lay.top + self.lay.plot_height * (self.high - value) / (self.high - self.low)

    def x(self, i):
        return self.plot_left + 16 + self.slot * (i + 0.5)

    def _grid(self):
        out = []
        for v in range(int(self.low), int(self.high) + 1, self.lay.grid_step):
            y = self.y(v)
            major = v % (self.lay.grid_step * 5) == 0
            out.append(f'<line class="grid{" major" if major else ""}" x1="{self.plot_left}" x2="{self.lay.width - 6}" '
                       f'y1="{y:.1f}" y2="{y:.1f}"/>')
            out.append(f'<text class="ax" x="{self.plot_left - 8}" y="{y + 4:.1f}">{fmt(v)}</text>')
        return out

    def _zone(self):
        lay, f = self.lay, self.forecast
        fx = self.zone_left + 26
        last = self.days[-1]
        lx = self.x(len(self.days) - 1)
        parts = [f'<rect class="zone" x="{self.zone_left}" y="{lay.top - 30}" width="{lay.zone_width - 6}" '
                 f'height="{lay.plot_height + 30}" rx="4"/>',
                 f'<text class="zh" x="{self.zone_left + 8}" y="{lay.top - 17}">Forecast</text>',
                 f'<text class="zd" x="{self.zone_left + 8}" y="{lay.top - 4}">{f["date"]}</text>']
        for key, cls, start in (("hi50", "hi", last["hi50"]), ("mid", "mid", last["close"]), ("lo50", "lo", last["lo50"])):
            parts.append(f'<line class="fc {cls}" x1="{lx:.1f}" y1="{self.y(start):.1f}" x2="{fx}" y2="{self.y(f[key]):.1f}"/>')
        labels = [("hi50", "high", fmt_high), ("mid", "mid", fmt_mid), ("lo50", "low", fmt_low)]
        ys = _spread([self.y(f[k]) for k, _, _ in labels], 18)
        for (key, word, show), y in zip(labels, ys):
            parts.append(f'<circle class="fcdot {word}" cx="{fx}" cy="{self.y(f[key]):.1f}" r="4"/>')
            parts.append(f'<text class="fcv {word}" x="{fx + 9}" y="{y + 4.5:.1f}">{show(f[key])}'
                         f'<tspan class="fcw"> {word}</tspan></text>')
        return parts

    def _lines(self):
        pts = lambda key: " ".join(f"{self.x(i):.1f},{self.y(d[key]):.1f}" for i, d in enumerate(self.days))
        return [f'<polyline class="line hi" points="{pts("hi50")}"/>',
                f'<polyline class="line lo" points="{pts("lo50")}"/>',
                f'<polyline class="line close" points="{pts("close")}"/>']

    def _points(self):
        parts = []
        n = len(self.days)
        every = self.slot >= self.lay.label_min_slot
        for i, d in enumerate(self.days):
            x, yh, yl, yc = self.x(i), self.y(d["hi50"]), self.y(d["lo50"]), self.y(d["close"])
            st = status(d)
            above = d["close"] <= (d["lo50"] + d["hi50"]) / 2  # the close label sits away from the nearer line
            y_close = yc - 11 if above else yc + 19
            labelled = every or i == n - 1 or i % 2 == 0
            if i in (0, n - 1) or st == "red":
                y_hi, y_lo = yh - 7, yl + 15
                if labelled and abs(y_hi - y_close) < 13:
                    y_hi = yh + 15  # under its own point instead of over the close label
                if labelled and abs(y_lo - y_close) < 13:
                    y_lo = yl - 7
                parts.append(f'<text class="v hi" x="{x:.1f}" y="{y_hi:.1f}">{fmt(d["hi50"])}</text>')
                parts.append(f'<text class="v lo" x="{x:.1f}" y="{y_lo:.1f}">{fmt(d["lo50"])}</text>')
            parts.append(f'<circle class="dot {st}" cx="{x:.1f}" cy="{yc:.1f}" r="6"/>')
            if labelled:
                parts.append(f'<text class="v close" x="{x:.1f}" y="{y_close:.1f}">{fmt(d["close"])}</text>')
        return parts + self._strip(every)

    def _strip(self, every):
        """Under the dates: every day's forecast high, close and low in three aligned rows (when they fit)."""
        base = self.lay.top + self.lay.plot_height
        parts = []
        for i, d in enumerate(self.days):
            x = self.x(i)
            day, month = d["date"].split()
            parts.append(f'<text class="day" x="{x:.1f}" y="{base + 18}">{day}</text>')
            parts.append(f'<text class="mon" x="{x:.1f}" y="{base + 31}">{month}</text>')
            if every:
                st = status(d)
                parts.append(f'<text class="s hi" x="{x:.1f}" y="{base + 50}">{fmt(d["hi50"])}</text>')
                parts.append(f'<text class="s close {st}" x="{x:.1f}" y="{base + 66}">{fmt(d["close"])}</text>')
                parts.append(f'<text class="s lo" x="{x:.1f}" y="{base + 82}">{fmt(d["lo50"])}</text>')
        if every:
            for word, dy in (("high", 50), ("close", 66), ("low", 82)):
                parts.append(f'<text class="sl" x="{self.plot_left - 6}" y="{base + dy}">{word}</text>')
        return parts

    def svg(self, aria):
        body = self._grid() + self._zone() + self._lines() + self._points()
        return (f'<svg class="chart" viewBox="0 0 {self.lay.width} {self.height}" role="img" aria-label="{aria}">'
                + "".join(body) + "</svg>")


def _spread(ys, gap):
    out = []
    for y in ys:
        if out and y - out[-1] < gap:
            y = out[-1] + gap
        out.append(y)
    return out
