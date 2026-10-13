"""Validation of a live 15:00 feature against its daily-close research version (story B7).

For every recorded day (a canonical A4 snapshot) that the panel also covers, both versions are computed for the same
context and compared: mean and largest absolute difference where both are numbers, and the share of days where the
condition differs (a number's condition is "above zero"; None is "not met"). Use rule (frozen per strategy in its
playbook, story D1): a live feature may drive paper decisions only with at least `min_days` compared days, a condition
agreement of at least `min_agreement` and, so that a feature that is never computed cannot pass vacuously, a live value
on at least `min_available` of the days. Disagreement days are listed for the red team.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import date

from .features import DecisionContext, Feature, FeatureValue, ResearchData

MIN_DAYS, MIN_AGREEMENT, MIN_AVAILABLE = 20, 0.90, 0.90  # story B7 proposal; the owner may set stricter values


@dataclass(frozen=True)
class LiveUseRule:
    min_days: int = MIN_DAYS
    min_agreement: float = MIN_AGREEMENT
    min_available: float = MIN_AVAILABLE


@dataclass(frozen=True)
class DayComparison:
    day: date
    live: FeatureValue
    close: FeatureValue

    @property
    def agrees(self) -> bool:
        return condition(self.live) == condition(self.close)

    @property
    def difference(self) -> float | None:
        numbers = all(isinstance(v, float) and not isinstance(v, bool) for v in (self.live, self.close))
        return abs(self.live - self.close) if numbers else None


def condition(value: FeatureValue) -> bool:
    """The policy condition a value stands for: a number above zero, a true flag; None is not met."""
    if value is None:
        return False
    return value if isinstance(value, bool) else value > 0


@dataclass(frozen=True)
class ValidationReport:
    live_feature: str
    close_feature: str
    comparisons: tuple[DayComparison, ...]
    rule: LiveUseRule

    @property
    def days(self) -> int:
        return len(self.comparisons)

    @property
    def agreement(self) -> float | None:
        return sum(c.agrees for c in self.comparisons) / self.days if self.days else None

    @property
    def available(self) -> float | None:
        return sum(c.live is not None for c in self.comparisons) / self.days if self.days else None

    @property
    def differences(self) -> list[float]:
        return [d for d in (c.difference for c in self.comparisons) if d is not None]

    @property
    def validated(self) -> bool:
        return (
            self.days >= self.rule.min_days
            and self.agreement >= self.rule.min_agreement
            and self.available >= self.rule.min_available
        )

    def summary(self) -> dict:
        diffs = self.differences
        return {
            "live_feature": self.live_feature, "close_feature": self.close_feature, "days": self.days,
            "agreement": self.agreement, "live_available": self.available,
            "mean_abs_difference": sum(diffs) / len(diffs) if diffs else None,
            "largest_abs_difference": max(diffs) if diffs else None, "validated": self.validated,
            "rule": asdict(self.rule),
            "disagreement_days": [c.day.isoformat() for c in self.comparisons if not c.agrees],
            "comparisons": [
                {"day": c.day.isoformat(), "live": c.live, "close": c.close, "agrees": c.agrees}
                for c in self.comparisons
            ],
        }  # fmt: skip


def validate(
    live: Feature,
    close: Feature,
    data: ResearchData,
    days: Sequence[date],
    context_for: Callable[[date], DecisionContext | None],
    rule: LiveUseRule | None = None,
) -> ValidationReport:
    """Compares the two versions on every recorded day the panel covers and that has a context."""
    comparisons = []
    for day in days:
        context = context_for(day)
        session = data.panel.session_on(day)
        if day not in data.snapshots or context is None or session is None or session.underlying is None:
            continue
        comparisons.append(DayComparison(day, live.value(data, day, context), close.value(data, day, context)))
    return ValidationReport(live.name, close.name, tuple(comparisons), rule or LiveUseRule())
