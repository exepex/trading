"""Chart 1: forecast middle (dashed blue) against the actual close (solid black), one point per trading day, the
last value of each line written, a title per day for hover. The morning variant adds today's forecast as one
labelled point on the right with its two ranges as a labelled vertical line. No shaded bands, no bars."""

import math
from dataclasses import dataclass

from linechart import fmt, fmt_high, fmt_low, fmt_mid, status


@dataclass(frozen=True)
class LinesLayout:
    width: int
    grid_step: int
    plot_height: int = 250
    top: int = 16
    axis_width: int = 54
    bottom: int = 34
    forecast_width: int = 0  # > 0 reserves room on the right for today's forecast point and its range line


def label_every(px_per_step):
    return 1 if px_per_step >= 13 else (2 if px_per_step >= 6.5 else 4)


class TwoLinesChart:
    def __init__(self, days, layout, forecast=None, date_every=1):
        self.days, self.lay, self.forecast, self.date_every = days, layout, forecast, date_every
        values = [v for d in days for v in (d["mid"], d["close"])]
        if forecast:
            values += [forecast["lo90"], forecast["hi90"]]
        step = layout.grid_step
        self.low = math.floor((min(values) - step * 0.5) / step) * step
        self.high = math.ceil((max(values) + step * 0.5) / step) * step
        self.plot_right = layout.width - 10 - layout.forecast_width
        self.slot = (self.plot_right - layout.axis_width - 10) / len(days)
        self.height = layout.top + layout.plot_height + layout.bottom
        self.label_every = label_every(layout.plot_height * step / (self.high - self.low))

    def y(self, value):
        return self.lay.top + self.lay.plot_height * (self.high - value) / (self.high - self.low)

    def x(self, i):
        return self.lay.axis_width + 10 + self.slot * (i + 0.5)

    def _grid(self):
        out = []
        for k, v in enumerate(range(int(self.low), int(self.high) + 1, self.lay.grid_step)):
            y = self.y(v)
            out.append(f'<line class="grid" x1="{self.lay.axis_width}" x2="{self.lay.width - 10}" y1="{y:.1f}" y2="{y:.1f}"/>')
            if k % self.label_every == 0:
                out.append(f'<text class="ax" x="{self.lay.axis_width - 6}" y="{y + 3.5:.1f}">{fmt(v)}</text>')
        return out

    def _lines(self):
        mids = " ".join(f"{self.x(i):.1f},{self.y(d['mid']):.1f}" for i, d in enumerate(self.days))
        closes = " ".join(f"{self.x(i):.1f},{self.y(d['close']):.1f}" for i, d in enumerate(self.days))
        return [f'<polyline class="mid" points="{mids}"/>', f'<polyline class="close" points="{closes}"/>']

    def _points(self):
        parts = []
        for i, d in enumerate(self.days):
            gap = d["close"] - d["mid"]
            tip = (f'{d["date_long"]}: forecast middle {fmt(d["mid"])}, actual close {fmt(d["close"])}, '
                   f'gap {gap:+,.0f} points ({status(d)})')
            parts.append(f'<g><title>{tip}</title>'
                         f'<circle class="pm" cx="{self.x(i):.1f}" cy="{self.y(d["mid"]):.1f}" r="3"/>'
                         f'<circle class="pc {status(d)}" cx="{self.x(i):.1f}" cy="{self.y(d["close"]):.1f}" r="4"/></g>')
        return parts

    def _end_labels(self):
        """The last value of each line, written left of the last point: the higher one above, the lower below."""
        last, x = self.days[-1], self.x(len(self.days) - 1) + 6
        ym, yc = self.y(last["mid"]), self.y(last["close"])
        up, down = (ym, yc) if ym < yc else (yc, ym)
        if down - up < 24:  # keep 24 px between the two labels
            up, down = (up + down) / 2 - 12, (up + down) / 2 + 12
        y_mid, y_close = (up - 7, down + 15) if ym < yc else (down + 15, up - 7)
        return [f'<text class="lv mid" style="text-anchor:end" x="{x:.1f}" y="{y_mid:.1f}">forecast {fmt(last["mid"])}</text>',
                f'<text class="lv close" style="text-anchor:end" x="{x:.1f}" y="{y_close:.1f}">close {fmt(last["close"])}</text>']

    def _dates(self):
        base, n = self.lay.top + self.lay.plot_height, len(self.days)
        parts = []
        for i, d in enumerate(self.days):
            if (n - 1 - i) % self.date_every == 0:
                last = i == n - 1 and not self.forecast
                parts.append(f'<text class="day" style="text-anchor:{"end" if last else "middle"}" '
                             f'x="{self.x(i) + (6 if last else 0):.1f}" y="{base + 16}">{d["date"]}</text>')
        return parts

    def _forecast(self):
        f, last = self.forecast, self.days[-1]
        x0, x1 = self.x(len(self.days) - 1), self.plot_right + 30
        parts = [f'<line class="mid" x1="{x0:.1f}" y1="{self.y(last["mid"]):.1f}" x2="{x1:.1f}" y2="{self.y(f["mid"]):.1f}"/>',
                 f'<line class="r90" x1="{x1:.1f}" x2="{x1:.1f}" y1="{self.y(f["hi90"]):.1f}" y2="{self.y(f["lo90"]):.1f}"/>',
                 f'<line class="r50" x1="{x1:.1f}" x2="{x1:.1f}" y1="{self.y(f["hi50"]):.1f}" y2="{self.y(f["lo50"]):.1f}"/>',
                 f'<circle class="pf" cx="{x1:.1f}" cy="{self.y(f["mid"]):.1f}" r="5"/>']
        labels = [("hi90", "faint", fmt_high, "almost certainly"), ("hi50", "num", fmt_high, "most likely"),
                  ("mid", "centre", fmt_mid, "forecast"), ("lo50", "num", fmt_low, "most likely"),
                  ("lo90", "faint", fmt_low, "almost certainly")]
        ys = _spread([self.y(f[k]) for k, _, _, _ in labels], 15)
        words = self.lay.forecast_width >= 140  # the phone drawing has room for the numbers only
        for (key, cls, show, word), y in zip(labels, ys):
            parts.append(f'<text class="fv {cls}" x="{x1 + 9:.1f}" y="{y + 4:.1f}">{show(f[key])}'
                         f'{f"<tspan class=\"fw\"> {word}</tspan>" if words else ""}</text>')
        parts.append(f'<text class="day fcd" x="{x1:.1f}" y="{self.lay.top + self.lay.plot_height + 16}">'
                     f'{f["date"].split(" ", 1)[1]}</text>')
        return parts

    def svg(self, aria):
        body = self._grid() + self._lines() + self._points() + self._end_labels() + self._dates()
        if self.forecast:
            body += self._forecast()
        return (f'<svg class="lines" viewBox="0 0 {self.lay.width} {self.height}" role="img" aria-label="{aria}">'
                + "".join(body) + "</svg>")


def _spread(ys, gap):
    out = []
    for y in ys:
        if out and y - out[-1] < gap:
            y = out[-1] + gap
        out.append(y)
    return out
