"""Hybrid's envelope (story F5's idea applied to forecasts): per question, Hybrid may answer from `width` below the
lowest available baseline to `width` above the highest, inside [0, 1]. A question with no baseline has no envelope,
so Hybrid answers "no forecast" there. An answer outside is refused for that question, never replaced by the rule
default (that would be imputing)."""

from __future__ import annotations

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
        bounds = {}
        for question, by_name in rules.items():
            values = [by_name[name] for name in BASELINES if by_name.get(name) is not None]
            low, high = (min(values) - width, max(values) + width) if values else (None, None)
            bounds[question] = (round(max(0.0, low), ROUNDING), round(min(1.0, high), ROUNDING)) if values else None
        return cls(bounds)

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
