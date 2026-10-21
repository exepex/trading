"""The reliability trend: the rolling 20-day share of closes inside "almost certainly" (the builder's rolling_90),
a dashed target line at 90% and a shaded warning zone below 80%. The drift and fluctuation detector."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TrendLayout:
    width: int
    plot_height: int = 110
    top: int = 14
    axis_width: int = 42
    bottom: int = 30


TARGET, FLOOR = 0.9, 0.8


class TrendChart:
    def __init__(self, dates, values, layout):
        self.dates, self.values, self.lay = dates, values, layout
        known = [v for v in values if v is not None]
        self.low = min(0.6, min(known) - 0.05) if known else 0.6
        self.high = 1.0
        self.slot = (layout.width - layout.axis_width - 16) / max(1, len(values))
        self.height = layout.top + layout.plot_height + layout.bottom

    def y(self, v):
        return self.lay.top + self.lay.plot_height * (self.high - v) / (self.high - self.low)

    def x(self, i):
        return self.lay.axis_width + 8 + self.slot * (i + 0.5)

    def state(self):
        """'steady' when the last value is at or above the floor, else 'watch'; 'too few' without data."""
        known = [v for v in self.values if v is not None]
        if not known:
            return "too few days"
        return "steady" if known[-1] >= FLOOR else "watch"

    def svg(self, aria):
        lay, right = self.lay, self.lay.width - 8
        parts = [f'<rect class="zone" x="{lay.axis_width}" y="{self.y(FLOOR):.1f}" width="{right - lay.axis_width}" '
                 f'height="{self.y(self.low) - self.y(FLOOR):.1f}"/>']
        v = 0.6
        while v <= 1.0001:
            if v >= self.low:
                parts.append(f'<line class="grid" x1="{lay.axis_width}" x2="{right}" y1="{self.y(v):.1f}" y2="{self.y(v):.1f}"/>')
                parts.append(f'<text class="ax" x="{lay.axis_width - 6}" y="{self.y(v) + 3.5:.1f}">{v:.0%}</text>')
            v += 0.1
        parts.append(f'<line class="target" x1="{lay.axis_width}" x2="{right}" y1="{self.y(TARGET):.1f}" y2="{self.y(TARGET):.1f}"/>')
        parts.append(f'<text class="tl" x="{lay.axis_width + 6}" y="{self.y(TARGET) + 12:.1f}">target 90%</text>')
        parts.append(f'<text class="tl warn" x="{lay.axis_width + 6}" y="{self.y(self.low) - 5:.1f}">warning zone, under 80%</text>')
        pts = [(self.x(i), self.y(val)) for i, val in enumerate(self.values) if val is not None]
        parts.append('<polyline class="trend" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '"/>')
        if pts:
            x, y = pts[-1]
            last = [val for val in self.values if val is not None][-1]
            parts.append(f'<circle class="tdot" cx="{x:.1f}" cy="{y:.1f}" r="4"/>')
            parts.append(f'<text class="tv" text-anchor="end" x="{x - 7:.1f}" y="{y + 4:.1f}">{last:.0%}</text>')
        base = lay.top + lay.plot_height
        n = len(self.dates)
        every = 5 if self.slot * 5 >= 60 else 7
        for i, d in enumerate(self.dates):
            if (n - 1 - i) % every == 0:
                last = i == n - 1
                parts.append(f'<text class="day" style="text-anchor:{"end" if last else "middle"}" '
                             f'x="{self.x(i) + (6 if last else 0):.1f}" y="{base + 16}">{d}</text>')
        return (f'<svg class="trend" viewBox="0 0 {lay.width} {self.height}" role="img" aria-label="{aria}">'
                + "".join(parts) + "</svg>")
