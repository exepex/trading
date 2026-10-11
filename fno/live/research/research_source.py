"""Where market-brief research comes from. Today: the stock tool's GitHub data files; later any database."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class NewsItem:
    """One scored news story about one company."""

    ticker: str
    title: str
    published_at: datetime
    sentiment: float | None  # -1..+1 from the stock tool's news analyst; None if not scored yet
    materiality: str | None  # low / medium / high
    status: str | None  # verification status, e.g. corroborated, rumour
    geopolitical: bool = False


@dataclass(frozen=True)
class RegimeReading:
    regime: str | None
    stress: bool
    major_events: list[str] = field(default_factory=list)


class ResearchSource(ABC):
    """Read-only access to the research. Implementations never raise for missing data: they return empty."""

    @property
    @abstractmethod
    def available(self) -> bool:
        """False when the source is not configured (the desk then trades on price signals only)."""

    def refresh(self) -> None:  # noqa: B027 - optional hook, most sources need nothing
        """Bring local copies up to date, if the source keeps any."""

    @abstractmethod
    def regime(self) -> RegimeReading | None: ...

    @abstractmethod
    def upcoming_earnings(self, from_day: date) -> dict[str, date]:
        """Next results date per ticker on or after from_day."""

    @abstractmethod
    def news_since(self, since: datetime) -> list[NewsItem]:
        """Scored news per ticker published at or after since, newest first."""

    @abstractmethod
    def model_prob_up(self, horizon_days: int) -> dict[str, float]:
        """Latest calibrated probability of a rise per ticker."""
