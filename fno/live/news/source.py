"""The interface every news source implements. Sources never raise for an empty answer; they raise on failure."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from .models import NewsItem


class NewsSource(ABC):
    name: str

    @abstractmethod
    def fetch(self, now: datetime) -> list[NewsItem]:
        """Headlines currently offered by the source (only new ones where the source supports asking for them)."""

    @property
    def min_interval_seconds(self) -> float:
        """The fastest the source itself says it changes (e.g. an RSS feed's cache time). 0 = no hint."""
        return 0.0
