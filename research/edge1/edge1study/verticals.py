"""Protocol section 7's price validity (revision 7, judge 473.1). NSE's option close is each strike's last trade, at
different times, so an illiquid strike's close can be impossible (a 300-wide spread at 392; a lower-strike put dearer
than a higher one). Prices are valid when each vertical (a sold leg and the bought leg of its type) is worth between
0 and its width, which catches two breaks that offset in the total, and the position is inside its payoff bounds
(an iron condor is never worth more than one width, though each vertical alone may be). A naked position (NS, NT)
has no vertical and is never touched. The all-trades proxy clips each failing vertical into [0, width] and then the
position value into its bounds."""

from __future__ import annotations

from collections.abc import Sequence

from fno.research_engine.structures import Leg, payoff_bounds, position_value


def verticals(legs: Sequence[Leg]) -> list[tuple[int, int, float]]:
    """(sold leg index, bought leg index, width) for each sold leg and each bought leg of its type."""
    return [(i, j, abs(bought.strike - sold.strike)) for i, sold in enumerate(legs) if not sold.bought
            for j, bought in enumerate(legs) if bought.bought and bought.kind == sold.kind]  # fmt: skip


def valid(legs: Sequence[Leg], prices: Sequence[float]) -> bool:
    pairs = verticals(legs)
    if not pairs:
        return True
    lowest, highest = payoff_bounds(legs)
    return (
        all(0.0 <= prices[i] - prices[j] <= w for i, j, w in pairs)
        and lowest <= position_value(legs, prices) <= highest
    )


def clipped(legs: Sequence[Leg], prices: Sequence[float]) -> list[float]:
    """The prices with each failing vertical's bought leg moved so the vertical is clipped into [0, width]."""
    out = list(prices)
    for i, j, width in verticals(legs):
        value = out[i] - out[j]
        if not 0.0 <= value <= width:
            out[j] = out[i] - min(max(value, 0.0), width)
    return out


def proxy_value(legs: Sequence[Leg], prices: Sequence[float]) -> float:
    """The position's value per unit at the clipped prices, clipped into its payoff bounds."""
    lowest, highest = payoff_bounds(legs)
    return min(max(position_value(legs, clipped(legs, prices)), lowest), highest)
