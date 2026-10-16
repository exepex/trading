"""Hybrid's envelope (story F5's idea applied to forecasts): per question, Hybrid may answer from `width` below the
lowest available baseline to `width` above the highest, inside [0, 1]. A question with no baseline has no envelope,
so Hybrid answers "no forecast" there. An answer outside is refused for that question, never replaced by the rule
default (that would be imputing)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..constants import BASELINE_BASE_RATE, BASELINE_MODEL, BASELINE_RISK_NEUTRAL
from .pointer import Rules

BASELINES = (BASELINE_RISK_NEUTRAL, BASELINE_BASE_RATE, BASELINE_MODEL)
ROUNDING = 6  # bounds are printed to the model and compared at this precision, so both sides see the same numbers


@dataclass(frozen=True)
class Envelope:
    bounds: dict[str, tuple[float, float] | None]  # question -> (low, high), or None: no envelope

    @classmethod
    def from_rules(cls, rules: Rules, width: float) -> Envelope:
        return cls({q: _bounds([by[n] for n in BASELINES if by.get(n) is not None], width) for q, by in rules.items()})

    @classmethod
    def around(cls, baseline: Mapping[str, float | None], width: float) -> Envelope:
        """Protocol v4: one primary baseline per question (its value, or None when it has none today)."""
        return cls({q: _bounds([] if value is None else [value], width) for q, value in baseline.items()})

    @classmethod
    def from_json(cls, bounds: dict) -> Envelope:
        """The envelope `as_json` wrote (an input's own statement of it)."""
        return cls({q: (tuple(b) if b else None) for q, b in bounds.items()})

    def problem(self, question: str, probability: float | None) -> str:
        """Why the answer breaks the envelope, or '' when it is inside (a "no forecast" always is)."""
        if probability is None:
            return ""
        allowed = self.bounds.get(question)
        if allowed is None:
            return "no envelope (no baseline today): only null is allowed"
        low, high = allowed
        return "" if low <= probability <= high else f"outside the envelope [{low}, {high}]"

    def as_json(self) -> dict[str, list[float] | None]:
        return {q: (list(b) if b else None) for q, b in sorted(self.bounds.items())}


def _bounds(values: list[float], width: float) -> tuple[float, float] | None:
    """From `width` below the lowest value to `width` above the highest, inside [0, 1]; None without a value."""
    if not values:
        return None
    return round(max(0.0, min(values) - width), ROUNDING), round(min(1.0, max(values) + width), ROUNDING)
