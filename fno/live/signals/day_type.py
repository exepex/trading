"""Trending or sideways? Option buyers lose most on sideways days: time decay and the bid-ask gap eat the premium
while the price goes nowhere. Efficiency of today's 5-minute path = net move / total distance travelled
(1.0 = a straight line, near 0 = back and forth), over the last hour: is it trending now?
Calibrated on 45 real sessions (12 Oct 2026): whole-day efficiency has a median of 0.12 (too noisy to use), the
last hour 0.26; 0.30 lets through roughly the most trending 45% of hours."""

from __future__ import annotations

from ..models import Candle, GuardVerdict
from .base import GuardRule, SymbolInputs

TOO_EARLY = "trend not known yet ({candles} of {needed} five-minute candles)"
SIDEWAYS = "sideways last hour: path efficiency {efficiency:.2f} below {limit:.2f}"
TRENDING = "trending last hour: path efficiency {efficiency:.2f}"


def path_efficiency(candles: list[Candle]) -> float | None:
    if not candles:
        return None
    points = [candles[0].open] + [c.close for c in candles]
    travelled = sum(abs(b - a) for a, b in zip(points, points[1:], strict=False))
    return abs(points[-1] - points[0]) / travelled if travelled > 0 else 0.0


class SidewaysDayGuard(GuardRule):
    name = "sideways_day"

    def evaluate(self, inputs: SymbolInputs) -> GuardVerdict:
        needed = self.settings.get("min_candles", 6)
        limit = self.settings.get("min_efficiency", 0.3)
        if len(inputs.candles) < needed:
            blocked = self.settings.get("block_until_known", True)
            return self.verdict(blocked, TOO_EARLY.format(candles=len(inputs.candles), needed=needed))
        efficiency = path_efficiency(inputs.candles[-self.settings.get("window_candles", 12) :])
        if efficiency < limit:
            return self.verdict(True, SIDEWAYS.format(efficiency=efficiency, limit=limit))
        return self.verdict(False, TRENDING.format(efficiency=efficiency))
