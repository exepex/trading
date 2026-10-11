"""What the option chain itself says: where option writers are adding positions today."""

from __future__ import annotations

from ...constants import OptionKind
from ..indicators import clamp
from ..models import SignalVote
from .base import SignalRule, SymbolInputs


class OptionWritingPressure(SignalRule):
    """Fresh put writing near the money means sellers expect support (bullish); fresh call writing, a ceiling.

    Uses today's change in open interest on the strikes around the money.
    """

    name = "option_writing"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        chain = inputs.chain
        if chain is None:
            return None
        strikes = chain.strikes()
        if not strikes:
            return None
        atm = strikes.index(chain.atm_strike())
        n = self.settings.get("strikes_each_side", 5)
        window = strikes[max(0, atm - n) : atm + n + 1]
        added_puts = self._added(chain, window, OptionKind.PUT.value)
        added_calls = self._added(chain, window, OptionKind.CALL.value)
        if added_puts is None or added_calls is None:
            return None
        total = abs(added_puts) + abs(added_calls)
        if total == 0:
            return None
        score = clamp((added_puts - added_calls) / total)
        return self.vote(
            score,
            f"near the money today: put OI {added_puts:+,.0f}, call OI {added_calls:+,.0f} contracts",
        )

    @staticmethod
    def _added(chain, strikes: list[float], kind: str) -> float | None:
        changes = [q.oi_change for k in strikes if (q := chain.get(k, kind)) is not None]
        if not changes or all(c is None for c in changes):
            return None  # the chain source does not report OI change (e.g. Groww)
        return sum(c or 0.0 for c in changes)
