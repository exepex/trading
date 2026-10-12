"""Foreign investors' index derivatives positioning (NSE participant-wise open interest) as a vote for indices."""

from __future__ import annotations

from ...constants import INDEX_UNDERLYINGS
from ..indicators import clamp
from ..models import SignalVote
from .base import SignalRule, SymbolInputs

REASON = "FIIs {fut} index futures longs ({shift:+.1%} vs recent average); options tilt {opt:+.2f}"


class FiiPositioningSignal(SignalRule):
    """Change, not level: FIIs adding index longs or call exposure against their recent average is bullish."""

    name = "fii_positioning"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        if inputs.symbol not in INDEX_UNDERLYINGS or inputs.fii is None:
            return None
        futures, options = inputs.fii.futures_shift(), inputs.fii.options_shift()
        if futures is None or options is None:
            return None
        s = self.settings
        score = s.get("futures_share", 0.6) * clamp(futures / s.get("futures_full_scale", 0.02)) + s.get(
            "options_share", 0.4
        ) * clamp(options / s.get("options_full_scale", 0.10))
        fut = "added" if futures > 0 else "cut"
        return self.vote(score, REASON.format(fut=fut, shift=futures, opt=options))
