"""Runs the news sources one request at a time and records each new story and each later sighting.

Never parallel: a single loop asks the most overdue source, waits the agreed gap, and asks the next. Nothing here
trades or alerts; the desk's analyst and guardian read the stories.
"""

from __future__ import annotations

import logging
import threading
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import requests

from ...constants import EVENT_NEWS_SIGHTING, EVENT_NEWS_STORY, NEWS_THEME_WORLD
from ...http_pacing import COOL_OFF_SECONDS, SourceCoolingOff
from ...models import IST
from ..results_store import ResultsStore
from .models import NewsItem, Story
from .poll_schedule import PollSchedule, SourcePlan
from .story_book import Arrival, StoryBook

log = logging.getLogger(__name__)

MAX_ITEM_AGE = timedelta(hours=3)  # older headlines are background, not news
RELOAD_DAYS = 1  # stories stored today and yesterday are reloaded after a restart
FETCH_ERRORS = (requests.RequestException, ValueError, ET.ParseError)


class NewsWatcher:
    def __init__(
        self,
        schedule: PollSchedule,
        book: StoryBook,
        store: ResultsStore,
        relevant_symbols: frozenset[str] | None = None,
        clock=None,
    ):
        """relevant_symbols: F&O underlyings and indices. Only stories about them, or world-risk stories, are stored;
        the rest is kept in memory for a day so its copies are still recognised. None = store every tagged story."""
        self.schedule = schedule
        self.book = book
        self.store = store
        self.relevant_symbols = relevant_symbols
        self.clock = clock or (lambda: datetime.now(IST))
        self.errors: dict[str, str] = {}
        self._stored: set[str] = set()

    def start(self, now: datetime) -> None:
        for record in self.store.payloads(EVENT_NEWS_STORY, (now - timedelta(days=RELOAD_DAYS)).date()):
            self.book.remember(record)
        self.schedule.start(now)

    def run_forever(self, stop: threading.Event) -> None:
        self.start(self.clock())
        while not stop.is_set():
            plan, at = self.schedule.next_request(self.clock())
            wait = (at - self.clock()).total_seconds()
            if wait > 0 and stop.wait(wait):
                break
            if plan is not None:
                self.poll(plan, self.clock())

    def poll(self, plan: SourcePlan, now: datetime) -> list[Arrival]:
        """Ask one source once. Its first answer after a start is baseline (already-published news)."""
        first_answer = plan.polls == 0
        try:
            items = plan.source.fetch(now)
        except SourceCoolingOff as exc:
            self._failed(plan, now, str(exc), pause=COOL_OFF_SECONDS)
            return []
        except FETCH_ERRORS as exc:
            self._failed(plan, now, str(exc))
            return []
        self.schedule.record(plan, now, ok=True)
        self.errors.pop(plan.name, None)
        arrivals = []
        for item in items:
            arrival = self.book.add(item, now, baseline=first_answer or self._too_old(item, now))
            if arrival and self._worth_storing(arrival):
                self._record(arrival, now)
                arrivals.append(arrival)
        return arrivals

    def _worth_storing(self, arrival: Arrival) -> bool:
        story = arrival.story
        if not arrival.is_new:
            return story.id in self._stored
        if NEWS_THEME_WORLD in story.themes:
            return True
        if self.relevant_symbols is None:
            return bool(story.symbols)
        return any(symbol in self.relevant_symbols for symbol in story.symbols)

    def recent(self, symbol: str, minutes: int) -> list[Story]:
        return self.book.recent(symbol, self.clock() - timedelta(minutes=minutes))

    def _failed(self, plan: SourcePlan, now: datetime, message: str, pause: float | None = None) -> None:
        self.schedule.record(plan, now, ok=False, pause_seconds=pause)
        if self.errors.get(plan.name) != message:
            log.warning("news source %s: %s", plan.name, message)
        self.errors[plan.name] = message

    @staticmethod
    def _too_old(item: NewsItem, now: datetime) -> bool:
        return item.published_at is not None and now - item.published_at > MAX_ITEM_AGE

    def _record(self, arrival: Arrival, now: datetime) -> None:
        story = arrival.story
        symbol = story.symbols[0] if story.symbols else None
        if arrival.is_new:
            self._stored.add(story.id)
            self.store.record(EVENT_NEWS_STORY, story.as_record(), now, symbol)
            return
        sighting = story.sightings[-1]
        self.store.record(
            EVENT_NEWS_SIGHTING,
            {
                "story_id": story.id,
                "source": sighting.source,
                "first_source": story.first_source,
                "seen_at": sighting.seen_at.isoformat(timespec="seconds"),
                "lag_seconds": round(arrival.lag_seconds),
                "outlets": len(story.outlets),
                "credibility": story.credibility.value,
            },
            now,
            symbol,
        )
