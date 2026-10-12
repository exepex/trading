"""Runs the news sources one request at a time and records each new story and each later sighting.

Never parallel: a single loop asks the most overdue source, waits the agreed gap, and asks the next. Nothing here
trades or alerts; the desk's analyst and guardian read the stories.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta

from ...constants import EVENT_NEWS_SIGHTING, EVENT_NEWS_STORY, NEWS_THEME_WORLD
from ...http_pacing import COOL_OFF_SECONDS, SourceCoolingOff
from ...models import IST
from ..results_store import ResultsStore
from .impact import NewsRoom
from .models import NewsItem
from .poll_schedule import PollSchedule, SourcePlan
from .story_book import Arrival

log = logging.getLogger(__name__)

MAX_ITEM_AGE = timedelta(hours=3)  # older headlines are background, not news
RELOAD_DAYS = 1  # stories stored today and yesterday are reloaded after a restart
UNEXPECTED_ERROR_PAUSE_SECONDS = 30


class NewsWatcher:
    def __init__(
        self,
        schedule: PollSchedule,
        room: NewsRoom,
        store: ResultsStore,
        relevant_symbols: frozenset[str] | None = None,
        clock=None,
    ):
        """relevant_symbols: F&O underlyings and indices. Only stories about them, or world-risk stories, are stored;
        the rest is kept in memory for a day so its copies are still recognised. None = store every tagged story."""
        self.schedule = schedule
        self.room = room
        self.book = room.book
        self.store = store
        self.relevant_symbols = relevant_symbols
        self.clock = clock or (lambda: datetime.now(IST))
        self.errors: dict[str, str] = {}
        self._stored: set[str] = set()

    def start(self, now: datetime) -> None:
        records = self.store.payloads(EVENT_NEWS_STORY, (now - timedelta(days=RELOAD_DAYS)).date())
        with self.room.lock:
            for record in records:
                self.book.remember(record)
        self.schedule.start(now)

    def run_forever(self, stop: threading.Event) -> None:
        self.start(self.clock())
        while not stop.is_set():
            try:
                plan, at = self.schedule.next_request(self.clock())
                wait = (at - self.clock()).total_seconds()
                if wait > 0 and stop.wait(wait):
                    break
                if plan is not None:
                    self.poll(plan, self.clock())
            except Exception:  # noqa: BLE001 - the watcher must outlive any one bad answer or bug
                log.exception("news watcher loop error; carrying on")
                stop.wait(UNEXPECTED_ERROR_PAUSE_SECONDS)

    def poll(self, plan: SourcePlan, now: datetime) -> list[Arrival]:
        """Ask one source once. Its first answer after a start is baseline (already-published news)."""
        first_answer = plan.polls == 0
        try:
            items = plan.source.fetch(now)
        except SourceCoolingOff as exc:
            self._failed(plan, self.clock(), str(exc), pause=COOL_OFF_SECONDS)
            return []
        except Exception as exc:  # noqa: BLE001 - any failure of one source: back off, keep the others going
            self._failed(plan, self.clock(), f"{type(exc).__name__}: {exc}")
            return []
        self.schedule.record(plan, self.clock(), ok=True)  # the gap to the next request starts when this one ends
        self.errors.pop(plan.name, None)
        arrivals = []
        for item in items:
            try:
                with self.room.lock:
                    arrival = self.book.add(item, now, baseline=first_answer or self._too_old(item, now))
                if arrival and self._worth_storing(arrival):
                    self._record(arrival, now)
                    arrivals.append(arrival)
            except Exception as exc:  # noqa: BLE001 - one malformed headline is skipped, the rest are kept
                log.warning("news source %s: skipped a malformed item: %s", plan.name, exc)
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
