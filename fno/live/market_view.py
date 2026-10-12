"""Combines signal votes and guards into one view per underlying."""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import Direction
from .models import MarketView, SignalVote
from .signals.base import GuardRule, SignalRule, SymbolInputs


@dataclass(frozen=True)
class ViewThresholds:
    """When the combined votes are enough to act. Values come from config.yaml `live.thresholds`."""

    min_score: float = 0.40  # |weighted score| to take a direction
    min_agreement: float = 0.65  # share of weighted votes on that side
    min_votes: int = 3  # rules that had an opinion
    strong_score: float = 0.55  # strong evidence allows a pricier single lot
    strong_agreement: float = 0.75
    strong_min_votes: int = 4

    @classmethod
    def from_config(cls, cfg: dict) -> ViewThresholds:
        return cls(**{k: v for k, v in (cfg or {}).items() if k in cls.__dataclass_fields__})


class MarketViewBuilder:
    def __init__(self, rules: list[SignalRule], guards: list[GuardRule], thresholds: ViewThresholds):
        self.rules = rules
        self.guards = guards
        self.thresholds = thresholds

    def build(self, inputs: SymbolInputs) -> MarketView:
        votes = [v for v in (rule.evaluate(inputs) for rule in self.rules) if v is not None]
        guards = [guard.evaluate(inputs) for guard in self.guards]
        score, agreement = combine(votes)
        return MarketView(
            symbol=inputs.symbol,
            direction=self._direction(score, agreement, len(votes)),
            score=round(score, 3),
            agreement=round(agreement, 3),
            votes=votes,
            guards=guards,
            strong_evidence=self._is_strong(score, agreement, len(votes)),
        )

    def _direction(self, score: float, agreement: float, n_votes: int) -> Direction:
        t = self.thresholds
        if n_votes < t.min_votes or abs(score) < t.min_score or agreement < t.min_agreement:
            return Direction.NEUTRAL
        return Direction.BULLISH if score > 0 else Direction.BEARISH

    def _is_strong(self, score: float, agreement: float, n_votes: int) -> bool:
        t = self.thresholds
        return n_votes >= t.strong_min_votes and abs(score) >= t.strong_score and agreement >= t.strong_agreement


def combine(votes: list[SignalVote]) -> tuple[float, float]:
    """Weighted mean score and the weighted share of votes agreeing with its sign."""
    total_weight = sum(v.weight for v in votes)
    if not total_weight:
        return 0.0, 0.0
    score = sum(v.score * v.weight for v in votes) / total_weight
    if score == 0:
        return 0.0, 0.0
    agreeing = sum(v.weight for v in votes if v.score * score > 0)
    return score, agreeing / total_weight
