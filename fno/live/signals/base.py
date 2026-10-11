"""Building blocks for signal rules and guards. Add a rule by subclassing; nothing else changes (open/closed)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from ..models import Candle, GuardVerdict, SignalVote, UnderlyingSnapshot
from ..research.research_context import ResearchSnapshot


@dataclass
class SymbolInputs:
    """Everything a rule may look at for one underlying in one scan."""

    symbol: str
    snapshot: UnderlyingSnapshot
    candles: list[Candle]
    benchmark_change_pct: float | None
    research: ResearchSnapshot
    banned: set[str] = field(default_factory=set)
    now: datetime | None = None

    @property
    def closes(self) -> list[float]:
        return [c.close for c in self.candles]


class SignalRule(ABC):
    """Scores one aspect of an underlying from -1 (bearish) to +1 (bullish), or abstains with None."""

    name: str = "rule"

    def __init__(self, weight: float, settings: dict | None = None):
        self.weight = weight
        self.settings = settings or {}

    def vote(self, score: float, reason: str) -> SignalVote:
        return SignalVote(rule=self.name, score=round(score, 3), weight=self.weight, reason=reason)

    @abstractmethod
    def evaluate(self, inputs: SymbolInputs) -> SignalVote | None:
        """Return a vote, or None when there is not enough data to have an opinion."""


class GuardRule(ABC):
    """A hard filter that blocks new trades on an underlying."""

    name: str = "guard"

    def __init__(self, settings: dict | None = None):
        self.settings = settings or {}

    def verdict(self, blocked: bool, reason: str) -> GuardVerdict:
        return GuardVerdict(guard=self.name, blocked=blocked, reason=reason)

    @abstractmethod
    def evaluate(self, inputs: SymbolInputs) -> GuardVerdict:
        """Return whether this underlying is blocked, and why."""
