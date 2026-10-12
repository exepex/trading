"""Merges headlines from many sources into stories, so the same news is handled once and each source's delay is
measured against whichever source had it first."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlsplit, urlunsplit

from .models import NewsItem, Sighting, Story
from .tagging import SymbolTagger

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    [
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "at",
        "by",
        "with",
        "from",
        "as",
        "is",
        "are",
        "was",
        "were",
        "be",
        "its",
        "it",
        "this",
        "that",
        "after",
        "over",
        "amid",
        "says",
        "said",
        "report",
        "reports",
        "today",
        "stock",
        "stocks",
        "share",
        "shares",
        "market",
        "markets",
        "news",
        "live",
        "update",
        "updates",
    ]
)
SAME_STORY_SIMILARITY = 0.6  # share of title words in common (Jaccard) for two headlines to be one story
MIN_SHARED_WORDS = 3


def title_tokens(title: str) -> frozenset[str]:
    return frozenset(t for t in TOKEN_PATTERN.findall(title.lower()) if t not in STOPWORDS and len(t) > 1)


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme, parts.netloc.lower().removeprefix("www."), parts.path.rstrip("/"), "", ""))


def similar(a: frozenset[str], b: frozenset[str]) -> bool:
    shared = len(a & b)
    return shared >= MIN_SHARED_WORDS and shared / max(len(a | b), 1) >= SAME_STORY_SIMILARITY


@dataclass(frozen=True)
class Arrival:
    """What the watcher should record for one headline: a new story, or a later sighting of a known one."""

    story: Story
    is_new: bool
    lag_seconds: float = 0.0


class StoryBook:
    def __init__(self, tagger: SymbolTagger, window: timedelta = timedelta(hours=24)):
        self.tagger = tagger
        self.window = window
        self.stories: list[Story] = []
        self._by_url: dict[str, Story] = {}

    def add(self, item: NewsItem, seen_at: datetime, baseline: bool = False) -> Arrival | None:
        """Returns None when there is nothing to report: this source already had the story, or the story is
        baseline (known before the watcher started, or too old to be news)."""
        self._forget_before(seen_at - self.window)
        tokens = title_tokens(item.title)
        story = self._find(item, tokens)
        if story is None:
            story = self._new_story(item, tokens, seen_at)
            story.baseline = baseline
            return None if baseline else Arrival(story, is_new=True)
        if story.baseline or any(s.source == item.source for s in story.sightings):
            return None
        story.sightings.append(Sighting(item.source, seen_at))
        return Arrival(story, is_new=False, lag_seconds=(seen_at - story.first_seen_at).total_seconds())

    def remember(self, record: dict) -> None:
        """Reload a stored story after a restart, so it is not reported again."""
        item = NewsItem(source=record["source"], title=record["title"], url=record.get("url", ""))
        story = self._new_story(item, title_tokens(item.title), datetime.fromisoformat(record["first_seen_at"]))
        story.id = record["id"]
        story.baseline = True

    def recent(self, symbol: str, since: datetime) -> list[Story]:
        return [s for s in self.stories if symbol in s.symbols and s.first_seen_at >= since]

    def _find(self, item: NewsItem, tokens: frozenset[str]) -> Story | None:
        url = canonical_url(item.url) if item.url else ""
        if url and url in self._by_url:
            return self._by_url[url]
        return next((s for s in reversed(self.stories) if similar(tokens, s.title_tokens)), None)

    def _new_story(self, item: NewsItem, tokens: frozenset[str], seen_at: datetime) -> Story:
        text = f"{item.title} {item.summary}"
        story = Story(
            id=hashlib.sha1(f"{item.title}|{seen_at.isoformat()}".encode()).hexdigest()[:12],
            title=item.title,
            url=item.url,
            published_at=item.published_at,
            symbols=self.tagger.symbols(item.title, item.symbols),
            themes=self.tagger.themes(text),
            summary=item.summary,
            sightings=[Sighting(item.source, seen_at)],
            title_tokens=tokens,
        )
        self.stories.append(story)
        if item.url:
            self._by_url[canonical_url(item.url)] = story
        return story

    def _forget_before(self, cutoff: datetime) -> None:
        if self.stories and self.stories[0].first_seen_at < cutoff:
            self.stories = [s for s in self.stories if s.first_seen_at >= cutoff]
            self._by_url = {u: s for u, s in self._by_url.items() if s.first_seen_at >= cutoff}
