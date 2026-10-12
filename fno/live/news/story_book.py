"""Merges headlines from many sources into stories, so the same news is handled once.

- The same outlet repeating or rewording a story is a duplicate: ignored.
- Another outlet carrying it is a confirmation: it raises the story's credibility and its delay behind the first
  source is measured.
- Two headlines are the same news when they share a link, or (for a stock) name the same company and share enough
  words or the same figures (e.g. "Rs 20,000 crore"), or (market-wide) share most of their words.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlsplit, urlunsplit

from .models import NewsItem, Sighting, Story
from .tagging import SymbolTagger

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
NUMBER_PATTERN = re.compile(r"\d[\d,]*(?:\.\d+)?")
STOPWORDS = frozenset(
    "a an the and or of to in on for at by with from as is are was were be its it this that after over amid says "  # noqa: SIM905
    "said report reports today stock stocks share shares market markets news live update updates rs cr crore".split()
)
YEARS = range(1990, 2036)  # "2026" in a headline is not a figure of the news
MIN_FIGURE_DIGITS = 3
SAME_HEADLINE_SIMILARITY = 0.6  # market-wide news: most words in common
SAME_COMPANY_SIMILARITY = 0.3  # news on the same company: fewer words needed
MIN_SHARED_WORDS = 3
MIN_SHARED_WORDS_WITH_FIGURE = 2


def title_tokens(title: str) -> frozenset[str]:
    return frozenset(t for t in TOKEN_PATTERN.findall(title.lower()) if t not in STOPWORDS and len(t) > 1)


def figures(text: str) -> frozenset[str]:
    found = set()
    for raw in NUMBER_PATTERN.findall(text):
        number = raw.replace(",", "").rstrip(".")
        digits = number.replace(".", "")
        if len(digits) >= MIN_FIGURE_DIGITS and not (number.isdigit() and int(number) in YEARS):
            found.add(number)
    return frozenset(found)


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme, parts.netloc.lower().removeprefix("www."), parts.path.rstrip("/"), "", ""))


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    return len(a & b) / max(len(a | b), 1)


@dataclass(frozen=True)
class Headline:
    """A headline prepared for matching."""

    tokens: frozenset[str]
    numbers: frozenset[str]
    symbols: tuple[str, ...]


def same_news(new: Headline, story: Story) -> bool:
    shared_symbols = set(new.symbols) & set(story.symbols)
    if new.symbols and story.symbols and not shared_symbols:
        return False  # different companies
    shared_words = len(new.tokens & story.title_tokens)
    if shared_symbols:
        same_figure = bool(new.numbers & story.numbers) and shared_words >= MIN_SHARED_WORDS_WITH_FIGURE
        similar = (
            shared_words >= MIN_SHARED_WORDS and jaccard(new.tokens, story.title_tokens) >= SAME_COMPANY_SIMILARITY
        )
        return same_figure or similar
    return shared_words >= MIN_SHARED_WORDS and jaccard(new.tokens, story.title_tokens) >= SAME_HEADLINE_SIMILARITY


@dataclass(frozen=True)
class Arrival:
    """What the watcher should record for one headline: a new story, or a confirmation by another outlet."""

    story: Story
    is_new: bool
    lag_seconds: float = 0.0


class StoryBook:
    def __init__(
        self,
        tagger: SymbolTagger,
        window: timedelta = timedelta(hours=24),
        outlet_of: dict[str, str] | None = None,
        primary_sources: frozenset[str] = frozenset(),
    ):
        self.tagger = tagger
        self.window = window
        self.outlet_of = outlet_of or {}
        self.primary_sources = primary_sources
        self.stories: list[Story] = []
        self._by_url: dict[str, Story] = {}

    def add(self, item: NewsItem, seen_at: datetime, baseline: bool = False) -> Arrival | None:
        """Returns None when there is nothing to report: a duplicate from an outlet that already carried the story,
        or a baseline story (known before the watcher started, or too old to be news)."""
        self._forget_before(seen_at - self.window)
        headline = Headline(
            title_tokens(item.title),
            figures(f"{item.title} {item.summary}"),
            self.tagger.symbols(item.title, item.symbols),
        )
        sighting = self._sighting(item.source, seen_at)
        story = self._find(item, headline)
        if story is None:
            story = self._new_story(item, headline, sighting)
            story.baseline = baseline
            return None if baseline else Arrival(story, is_new=True)
        if story.baseline or sighting.outlet in story.outlets:
            return None
        story.sightings.append(sighting)
        return Arrival(story, is_new=False, lag_seconds=(seen_at - story.first_seen_at).total_seconds())

    def remember(self, record: dict) -> None:
        """Reload a stored story after a restart, so it is not reported again."""
        item = NewsItem(source=record["source"], title=record["title"], url=record.get("url", ""))
        seen_at = datetime.fromisoformat(record["first_seen_at"])
        headline = Headline(title_tokens(item.title), figures(item.title), tuple(record.get("symbols", ())))
        story = self._new_story(item, headline, self._sighting(item.source, seen_at))
        story.id = record["id"]
        story.baseline = True

    def recent(self, symbol: str, since: datetime) -> list[Story]:
        return [s for s in self.stories if symbol in s.symbols and s.first_seen_at >= since and not s.baseline]

    def _sighting(self, source: str, seen_at: datetime) -> Sighting:
        return Sighting(source, seen_at, self.outlet_of.get(source, source), source in self.primary_sources)

    def _find(self, item: NewsItem, headline: Headline) -> Story | None:
        url = canonical_url(item.url) if item.url else ""
        if url and url in self._by_url:
            return self._by_url[url]
        return next((s for s in reversed(self.stories) if same_news(headline, s)), None)

    def _new_story(self, item: NewsItem, headline: Headline, sighting: Sighting) -> Story:
        story = Story(
            id=hashlib.sha1(f"{item.title}|{sighting.seen_at.isoformat()}".encode()).hexdigest()[:12],
            title=item.title,
            url=item.url,
            published_at=item.published_at,
            symbols=headline.symbols,
            themes=self.tagger.themes(f"{item.title} {item.summary}"),
            summary=item.summary,
            sightings=[sighting],
            title_tokens=headline.tokens,
            numbers=headline.numbers,
        )
        self.stories.append(story)
        if item.url:
            self._by_url[canonical_url(item.url)] = story
        return story

    def _forget_before(self, cutoff: datetime) -> None:
        if self.stories and self.stories[0].first_seen_at < cutoff:
            self.stories = [s for s in self.stories if s.first_seen_at >= cutoff]
            self._by_url = {u: s for u, s in self._by_url.items() if s.first_seen_at >= cutoff}
