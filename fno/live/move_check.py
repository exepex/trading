"""Move needed vs move likely: will the underlying plausibly move far enough, soon enough, for this option to reach
its target before time decay wins? Needed move solves delta*dS + gamma*dS^2/2 = target gain + decay over the hold;
the likely move is one standard deviation of the market's own expectation (at-the-money IV) over the same hold."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from ..analytics import Greeks, atm_iv
from ..models import OptionChain

PERCENT = 100.0
DAYS_PER_YEAR = 365.0
PROBLEM = "needs more than {limit:g}x the move the market expects"
DETAIL = "needs a {needed:,.0f}-point move, {ratio:.2f}x the {likely:,.0f} points the market expects in {days:g} days"


def move_needed(gain: float, greeks: Greeks) -> float | None:
    """Underlying points for the option to gain `gain` per unit (delta and gamma; None if it never can)."""
    delta, gamma = abs(greeks.delta), max(greeks.gamma, 0.0)
    if delta <= 0 and gamma <= 0:
        return None
    if gamma <= 0:
        return gain / delta
    return (-delta + sqrt(delta * delta + 2 * gamma * gain)) / gamma


@dataclass(frozen=True)
class MoveCheck:
    max_needed_to_likely: float = 1.5
    hold_days: float = 2.0  # the longest the desk holds a trade
    take_profit_pct: float = 60.0
    risk_free_rate: float = 0.065

    def measure(self, chain: OptionChain, price: float, greeks: Greeks) -> tuple[float, float] | None:
        """(points needed, points likely) or None when it cannot be judged (no IV, no spot, no sensitivity)."""
        iv = atm_iv(chain, self.risk_free_rate)
        if iv is None or chain.spot <= 0:
            return None
        likely = chain.spot * iv * sqrt(self.hold_days / DAYS_PER_YEAR)
        decay = max(-greeks.theta, 0.0) * self.hold_days
        needed = move_needed(price * self.take_profit_pct / PERCENT + decay, greeks)
        return None if needed is None or likely <= 0 else (needed, likely)

    def problem(self, chain: OptionChain, price: float, greeks: Greeks) -> str | None:
        measured = self.measure(chain, price, greeks)
        if measured and measured[0] / measured[1] > self.max_needed_to_likely:
            return PROBLEM.format(limit=self.max_needed_to_likely)
        return None

    def detail(self, chain: OptionChain, price: float, greeks: Greeks) -> str | None:
        measured = self.measure(chain, price, greeks)
        if measured is None:
            return None
        needed, likely = measured
        return DETAIL.format(needed=needed, ratio=needed / likely, likely=likely, days=self.hold_days)
