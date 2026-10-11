"""Derivatives positioning: what futures open interest says about fresh buying or selling."""

from __future__ import annotations

from ...constants import OiBuildup
from ..models import SignalVote, oi_buildup
from .base import SignalRule, SymbolInputs

BUILDUP_SCORES = {
    OiBuildup.LONG_BUILDUP: 1.0,
    OiBuildup.SHORT_COVERING: 0.5,
    OiBuildup.LONG_UNWINDING: -0.5,
    OiBuildup.SHORT_BUILDUP: -1.0,
}


class FuturesOiBuildup(SignalRule):
    name = "oi_buildup"

    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        snap = inputs.snapshot
        reading = oi_buildup(snap.day_change_pct, snap.oi_change_pct, self.settings.get("min_oi_change_pct", 2.0))
        if reading is OiBuildup.UNCLEAR:
            return None
        return self.vote(
            BUILDUP_SCORES[reading],
            f"{reading.value}: price {snap.day_change_pct:+.2f}%, open interest {snap.oi_change_pct:+.1f}%",
        )
