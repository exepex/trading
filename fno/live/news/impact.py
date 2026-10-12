"""Turns recent stories into one number per underlying: how strongly the news pushes its price, and which way.

impact of a story = type weight x credibility weight x relevance x freshness x direction
The weights below are starting guesses from market experience; the desk grades the `fast_news` signal against later
price moves (`live signal-report`) and the weights are tuned from that evidence.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ...constants import INDEX_UNDERLYINGS, NEWS_THEME_WORLD, NewsCredibility, NewsEventType
from .classifier import direction, event_type
from .models import Story
from .story_book import StoryBook

DEFAULT_TYPE_WEIGHTS = {
    NewsEventType.RESULTS: 1.0,
    NewsEventType.GUIDANCE: 0.9,
    NewsEventType.REGULATORY: 0.9,
    NewsEventType.ORDER: 0.7,
    NewsEventType.MACRO: 0.7,
    NewsEventType.CORPORATE_ACTION: 0.6,
    NewsEventType.DEAL_FLOW: 0.6,
    NewsEventType.MANAGEMENT: 0.5,
    NewsEventType.RATING: 0.4,
    NewsEventType.OTHER: 0.2,
    NewsEventType.ROUTINE: 0.0,
}
DEFAULT_CREDIBILITY_WEIGHTS = {
    NewsCredibility.EXCHANGE_FILING: 1.0,
    NewsCredibility.WIDELY_REPORTED: 0.9,
    NewsCredibility.CORROBORATED: 0.7,
    NewsCredibility.SINGLE_SOURCE: 0.4,
}
STRONG_CREDIBILITY = (NewsCredibility.EXCHANGE_FILING, NewsCredibility.WIDELY_REPORTED, NewsCredibility.CORROBORATED)
REASON_TEMPLATE = "{event}, {credibility}, {age:.0f} min ago: {title}"


@dataclass(frozen=True)
class ScoredStory:
    story: Story
    event: NewsEventType
    direction: float
    weight: float  # everything except direction
    age_minutes: float
    relevance: float = 1.0  # 1.0 = the underlying's own news; less for world news

    @property
    def importance(self) -> float:
        """How big the story is, before scaling by how much it concerns this underlying."""
        return self.weight / self.relevance if self.relevance else 0.0

    @property
    def impact(self) -> float:
        return self.direction * self.weight

    @property
    def reason(self) -> str:
        return REASON_TEMPLATE.format(
            event=self.event.value,
            credibility=self.story.credibility.value,
            age=self.age_minutes,
            title=self.story.title[:90],
        )


@dataclass(frozen=True)
class NewsPulse:
    """The news on one underlying right now."""

    symbol: str
    score: float  # -1..+1: sum of story impacts, scaled
    stories: tuple[ScoredStory, ...] = field(default_factory=tuple)

    @property
    def strongest(self) -> ScoredStory | None:
        return max(self.stories, key=lambda s: abs(s.impact), default=None)

    def major_unclear(self, within_minutes: float, min_weight: float) -> ScoredStory | None:
        """A fresh, credible, important story whose direction the headline does not tell: wait for the market.
        Importance is judged before relevance, so big world news counts for the indices it moves; for a single
        stock only its own news counts (world news reaches stocks through the indices and the backdrop)."""
        for s in self.stories:
            concerns = s.relevance >= 1.0 or self.symbol in INDEX_UNDERLYINGS
            fresh = s.age_minutes <= within_minutes and s.story.credibility in STRONG_CREDIBILITY
            if concerns and fresh and s.direction == 0 and s.importance >= min_weight:
                return s
        return None


@dataclass
class ImpactSettings:
    lookback_minutes: float = 120
    half_life_minutes: float = 45
    full_scale: float = 1.0  # summed impact that counts as the strongest possible news push
    world_relevance_index: float = 0.6  # world news for NIFTY/BANKNIFTY/FINNIFTY
    world_relevance_stock: float = 0.2  # world news for a single stock (its own news matters far more)
    type_weights: dict = field(default_factory=lambda: dict(DEFAULT_TYPE_WEIGHTS))
    credibility_weights: dict = field(default_factory=lambda: dict(DEFAULT_CREDIBILITY_WEIGHTS))

    @classmethod
    def from_config(cls, cfg: dict | None) -> ImpactSettings:
        cfg = dict(cfg or {})
        settings = cls(**{k: v for k, v in cfg.items() if k not in ("type_weights", "credibility_weights")})
        for key, enum in (("type_weights", NewsEventType), ("credibility_weights", NewsCredibility)):
            for name, value in (cfg.get(key) or {}).items():
                getattr(settings, key)[enum(name.replace("_", " "))] = value
        return settings


class NewsRoom:
    """Shared by the news watcher (writes stories) and the scanner and runner (read pulses). Thread-safe."""

    def __init__(self, book: StoryBook, settings: ImpactSettings | None = None):
        self.book = book
        self.settings = settings or ImpactSettings()
        self.lock = threading.Lock()

    def pulse(self, symbol: str, now: datetime) -> NewsPulse:
        s = self.settings
        since = now - timedelta(minutes=s.lookback_minutes)
        with self.lock:
            own = self.book.recent(symbol, since)
            world = [st for st in self.book.recent_theme(NEWS_THEME_WORLD, since) if st not in own]
        world_relevance = s.world_relevance_index if symbol in INDEX_UNDERLYINGS else s.world_relevance_stock
        scored = [self._score(st, now, 1.0) for st in own] + [self._score(st, now, world_relevance) for st in world]
        scored = [x for x in scored if x.weight > 0]
        total = sum(x.impact for x in scored)
        return NewsPulse(symbol, max(-1.0, min(1.0, total / s.full_scale)), tuple(scored))

    def _score(self, story: Story, now: datetime, relevance: float) -> ScoredStory:
        s = self.settings
        event = event_type(story)
        age = max((now - story.first_seen_at).total_seconds() / 60, 0.0)
        freshness = 0.5 ** (age / s.half_life_minutes)
        weight = s.type_weights[event] * s.credibility_weights[story.credibility] * relevance * freshness
        return ScoredStory(story, event, direction(story), weight, age, relevance)
