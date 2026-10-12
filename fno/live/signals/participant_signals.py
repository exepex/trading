"""Foreign investors' index derivatives positioning (NSE participant-wise open interest) as a vote for indices."""

from __future__ import annotations

from ...constants import INDEX_UNDERLYINGS
from ..indicators import clamp
from ..models import SignalVote
from .base import SignalRule, SymbolInputs

REASON = (
    "FII index futures long share {shift:+.1%} pts vs its recent average; "
    "options tilt change {opt:+.2f} (data of {day:%d %b})"
)
MAX_DATA_AGE_DAYS = 5  # the latest file must be from the last session or so (a long weekend is 4 days)


class FiiPositioningSignal(SignalRule):
    """Change, not level: FIIs adding index longs or call exposure against their recent average is bullish."""

    name = "fii_positioning"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        if inputs.symbol not in INDEX_UNDERLYINGS or inputs.fii is None or inputs.fii.latest is None:
            return None
        latest = inputs.fii.latest.day
        if inputs.now is not None and (inputs.now.date() - latest).days > self.settings.get(
            "max_age_days", MAX_DATA_AGE_DAYS
        ):
            return None  # stale positioning is not today's positioning
        futures, options = inputs.fii.futures_shift(), inputs.fii.options_shift()
        if futures is None or options is None:
            return None
        s = self.settings
        score = s.get("futures_share", 0.6) * clamp(futures / s.get("futures_full_scale", 0.02)) + s.get(
            "options_share", 0.4
        ) * clamp(options / s.get("options_full_scale", 0.10))
        return self.vote(score, REASON.format(shift=futures, opt=options, day=latest))
