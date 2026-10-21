"""The one chart style of v7 (owner, 21 Oct): a fan chart. X = trading dates; a light corridor = "almost
certainly", a darker corridor = "most likely" (areas between the forecast high and low), a solid line = the actual
close with a dot per day coloured by the result; the last value and every miss written. In the morning the same
chart runs over the last 10 days and extends the corridors to today's forecast with a dashed edge."""

import math
from dataclasses import dataclass

from linechart import fmt, fmt_high, fmt_low, fmt_mid, status


@dataclass(frozen=True)
class FanLayout:
    width: int
    grid_step: int
    plot_height: int = 220
    top: int = 18
    axis_width: int = 50
    bottom: int = 34
    forecast_width: int = 0  # > 0 reserves room on the right for today's forecast corridor and its labels


class FanChart:
    def __init__(self, days, layout, forecast=None, date_every=1):
        self.days, self.lay, self.forecast, self.date_every = days, layout, forecast, date_every
        values = [v for d in days for v in (d["lo90"], d["hi90"], d["close"])]
        if forecast:
            values += [forecast["lo90"], forecast["hi90"]]
        step = layout.grid_step
        self.low = math.floor((min(values) - step * 0.4) / step) * step
        self.high = math.ceil((max(values) + step * 0.4) / step) * step
        self.plot_right = layout.width - 8 - layout.forecast_width
        px_per_step = layout.plot_height * step / (self.high - self.low)
        self.label_every = 1 if px_per_step >= 13 else 2  # a number on every gridline when they are 13 px apart
        self.slot = (self.plot_right - layout.axis_width - 8) / len(days)
        self.height = layout.top + layout.plot_height + layout.bottom

    def y(self, value):
        return self.lay.top + self.lay.plot_height * (self.high - value) / (self.high - self.low)

    def x(self, i):
        return self.lay.axis_width + 8 + self.slot * (i + 0.5)

    def _grid(self):
        out = []
        for k, v in enumerate(range(int(self.low), int(self.high) + 1, self.lay.grid_step)):
            y = self.y(v)
            out.append(f'<line class="grid" x1="{self.lay.axis_width}" x2="{self.lay.width - 8}" y1="{y:.1f}" y2="{y:.1f}"/>')
            if k % self.label_every == 0:
                out.append(f'<text class="ax" x="{self.lay.axis_width - 6}" y="{y + 3.5:.1f}">{fmt(v)}</text>')
        return out

    def _area(self, lo, hi, cls):
        top = " ".join(f"{self.x(i):.1f},{self.y(d[hi]):.1f}" for i, d in enumerate(self.days))
        bottom = " ".join(f"{self.x(i):.1f},{self.y(d[lo]):.1f}" for i, d in reversed(list(enumerate(self.days))))
        return f'<polygon class="{cls}" points="{top} {bottom}"/>'

    def _closes(self):
        pts = " ".join(f"{self.x(i):.1f},{self.y(d['close']):.1f}" for i, d in enumerate(self.days))
        parts = [f'<polyline class="close" points="{pts}"/>']
        n, placed = len(self.days), []
        for i, d in enumerate(self.days):
            st, x, yc = status(d), self.x(i), self.y(d["close"])
            parts.append(f'<circle class="dot {st}" cx="{x:.1f}" cy="{yc:.1f}" r="4.5"/>')
            if st == "red" or i == n - 1:
                last = i == n - 1
                lx = min(x + 4 if last else x, self.plot_right - 26)
                # the label goes to the side away from the neighbouring closes, so the line never crosses it
                near = [self.y(self.days[j]["close"]) for j in (i - 1, i + 1) if 0 <= j < n]
                above = sum(near) / len(near) > yc if near else d["close"] >= d["mid"]
                # clear of the neighbouring dots too, so the line never runs through the number
                y = min([yc] + near) - 9 if above else max([yc] + near) + 16
                y = _free_y(lx, y, placed, above)
                placed.append((lx, y))
                parts.append(f'<text class="v {st}" style="text-anchor:{"end" if last else "middle"}" x="{lx:.1f}" '
                             f'y="{y:.1f}">{fmt(d["close"])}</text>')
        return parts

    def _dates(self):
        base = self.lay.top + self.lay.plot_height
        parts = []
        n = len(self.days)
        for i, d in enumerate(self.days):
            if (n - 1 - i) % self.date_every == 0:  # counted back from the last day, so the last is always written
                parts.append(f'<text class="day" x="{self.x(i):.1f}" y="{base + 16}">{d["date"]}</text>')
        return parts

    def _forecast(self):
        f, last = self.forecast, self.days[-1]
        x0, x1 = self.x(len(self.days) - 1), self.plot_right + 26
        parts = []
        for lo, hi, cls in (("lo90", "hi90", "r90"), ("lo50", "hi50", "r50")):
            parts.append(f'<polygon class="{cls} fc" points="{x0:.1f},{self.y(last[hi]):.1f} {x1:.1f},{self.y(f[hi]):.1f} '
                         f'{x1:.1f},{self.y(f[lo]):.1f} {x0:.1f},{self.y(last[lo]):.1f}"/>')
            parts.append(f'<line class="edge" x1="{x0:.1f}" y1="{self.y(last[hi]):.1f}" x2="{x1:.1f}" y2="{self.y(f[hi]):.1f}"/>')
            parts.append(f'<line class="edge" x1="{x0:.1f}" y1="{self.y(last[lo]):.1f}" x2="{x1:.1f}" y2="{self.y(f[lo]):.1f}"/>')
        parts.append(f'<line class="edge mid" x1="{x0:.1f}" y1="{self.y(last["close"]):.1f}" x2="{x1:.1f}" y2="{self.y(f["mid"]):.1f}"/>')
        labels = [("hi90", "faint", fmt_high), ("hi50", "num", fmt_high), ("mid", "centre", fmt_mid),
                  ("lo50", "num", fmt_low), ("lo90", "faint", fmt_low)]
        ys = _spread([self.y(f[k]) for k, _, _ in labels], 14)
        for (key, cls, show), y in zip(labels, ys):
            parts.append(f'<text class="fv {cls}" x="{x1 + 6:.1f}" y="{y + 4:.1f}">{show(f[key])}</text>')
        parts.append(f'<text class="day fcd" x="{x1:.1f}" y="{self.lay.top + self.lay.plot_height + 16}">'
                     f'{f["date"].split(" ", 1)[1]}</text>')
        parts.append(f'<text class="zh" x="{x1 + 6:.1f}" y="{self.lay.top - 4}">forecast</text>')
        return parts

    def svg(self, aria):
        body = self._grid() + [self._area("lo90", "hi90", "r90"), self._area("lo50", "hi50", "r50")]
        body += self._closes() + self._dates()
        if self.forecast:
            body += self._forecast()
        return (f'<svg class="fan" viewBox="0 0 {self.lay.width} {self.height}" role="img" aria-label="{aria}">'
                + "".join(body) + "</svg>")


def _free_y(x, y, placed, above, dx=44, dy=12):
    """A label y that does not sit on an earlier label: when one is within dx and dy, step further away from
    the line (up for a label above its dot, down for one below)."""
    for px, py in placed:
        if abs(px - x) < dx and abs(py - y) < dy:
            y = py - dy - 1 if above else py + dy + 1
    return y


def _spread(ys, gap):
    out = []
    for y in ys:
        if out and y - out[-1] < gap:
            y = out[-1] + gap
        out.append(y)
    return out
