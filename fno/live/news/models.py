"""What a news source returns and what the watcher keeps."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ...constants import NewsCredibility

SUMMARY_MAX_CHARS = 300


@dataclass(frozen=True)
class NewsItem:
    """One headline as a single source delivered it."""

    source: str
    title: str
    url: str = ""
    published_at: datetime | None = None
    summary: str = ""
    symbols: tuple[str, ...] = ()  # tickers the source itself tagged (e.g. Marketaux entities, NSE filings)
    sentiment: float | None = None  # -1..+1 when the source scores it (Marketaux)


CORROBORATED_OUTLETS = 2
WIDELY_REPORTED_OUTLETS = 3


@dataclass(frozen=True)
class Sighting:
    source: str
    seen_at: datetime
    outlet: str = ""  # the publisher behind the source: two feeds of one newspaper are one outlet
    primary: bool = False  # an exchange filing


@dataclass
class Story:
    """One piece of news, however many sources carried it. The first sighting is the fastest source."""

    id: str
    title: str
    url: str
    published_at: datetime | None
    symbols: tuple[str, ...]
    themes: tuple[str, ...]
    summary: str
    sightings: list[Sighting] = field(default_factory=list)
    title_tokens: frozenset[str] = frozenset()
    numbers: frozenset[str] = frozenset()  # amounts and figures in the news (e.g. 20000, 7.5): strong match evidence
    sentiment: float | None = None
    baseline: bool = False  # already known when the watcher started, or too old to be news: never reported

    @property
    def first_seen_at(self) -> datetime:
        return self.sightings[0].seen_at

    @property
    def first_source(self) -> str:
        return self.sightings[0].source

    @property
    def outlets(self) -> set[str]:
        return {s.outlet or s.source for s in self.sightings}

    @property
    def credibility(self) -> NewsCredibility:
        if any(s.primary for s in self.sightings):
            return NewsCredibility.EXCHANGE_FILING
        count = len(self.outlets)
        if count >= WIDELY_REPORTED_OUTLETS:
            return NewsCredibility.WIDELY_REPORTED
        return NewsCredibility.CORROBORATED if count >= CORROBORATED_OUTLETS else NewsCredibility.SINGLE_SOURCE

    def as_record(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.first_source,
            "published_at": self.published_at.isoformat(timespec="seconds") if self.published_at else None,
            "first_seen_at": self.first_seen_at.isoformat(timespec="seconds"),
            "symbols": list(self.symbols),
            "themes": list(self.themes),
            "summary": self.summary[:SUMMARY_MAX_CHARS],
            "credibility": self.credibility.value,
        }
