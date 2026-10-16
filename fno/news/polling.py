"""One poll of every feed (story A19, scopes 4, 5 and 8): fetch, parse, keep only what is unseen, and note each
feed's outcome in the heartbeat line. Feed failures, staleness, a feed reaching past the memory and clock skew open
or close their episodes here; nothing of an item is printed."""

from __future__ import annotations

from datetime import datetime, timedelta

from .episodes import Episodes
from .fetch import FeedFetch, NewsSource
from .identity import item_id, version_of
from .memory import SeenMemory
from .names import (
    BEYOND_WINDOW,
    CLOCK,
    FAILED,
    HTTP_ERROR,
    ITEM_LINE,
    NEW,
    NO_ITEMS,
    NO_TIMES,
    NOT_MODIFIED,
    NOT_XML,
    NOTHING_NEW,
    POLL_LINE,
    STALE,
)
from .parse import FeedProblem, NewsItem, parse_feed
from .stale import StaleRule

FETCH_KINDS = (HTTP_ERROR, NOT_XML, NO_ITEMS)
MAX_SKEW = timedelta(seconds=5)
SKEW_DETAIL = "{feed}: our clock differs from its Date header by {seconds:.1f} s"


class FeedPoller:
    def __init__(self, sources: list[NewsSource], memory: SeenMemory, episodes: Episodes, stale: StaleRule,
                 run_id: str):  # fmt: skip
        self.sources, self.memory, self.episodes, self.stale, self.run_id = sources, memory, episodes, stale, run_id

    def poll(self, now: datetime) -> list[dict]:
        """The lines of one poll: its heartbeat first, then every unseen item or version."""
        outcomes, items, skews = {}, [], []
        for source in self.sources:
            outcome, lines, skew = self._poll_feed(source, now)
            outcomes[source.feed.id] = outcome
            items += lines
            if skew is not None and abs(skew) > MAX_SKEW.total_seconds():
                skews.append(SKEW_DETAIL.format(feed=source.feed.id, seconds=skew))
        self.memory.last_heartbeat = now.isoformat()
        if skews:
            self.episodes.fail(CLOCK, CLOCK, skews[0])
        elif any(o["outcome"] in (NEW, NOTHING_NEW, NOT_MODIFIED) for o in outcomes.values()):
            self.episodes.ok(CLOCK)
        return [{"line": POLL_LINE, "polled_at": now.isoformat(), "run_id": self.run_id, "feeds": outcomes}, *items]

    def _poll_feed(self, source: NewsSource, now: datetime) -> tuple[dict, list[dict], float | None]:
        feed = source.feed
        try:
            fetch = source.fetch()
            items = [] if fetch.not_modified else parse_feed(fetch.data, feed)
        except FeedProblem as problem:
            self.episodes.fail(feed.id, problem.kind, f"{feed.id}: {problem}")
            self._check_stale(source, now)
            return {"outcome": f"{FAILED}:{problem.kind}", "listed": 0, "new": 0}, [], None
        self.episodes.ok(feed.id, FETCH_KINDS)
        first_poll = feed.id not in self.memory.last_poll
        previous = self.memory.mark_poll(feed, fetch.received_at)
        records = self.memory.observe(feed, items, fetch.received_at, first_poll)
        skew = _skew(fetch)
        lines = [self._line(source, fetch, item, record, previous, skew) for item, record in _matched(items, records)]
        self._check_times(source, items)
        self._check_window(source, records)
        self._check_stale(source, now)
        outcome = NOT_MODIFIED if fetch.not_modified else NEW if lines else NOTHING_NEW
        return {"outcome": outcome, "listed": len(items), "new": len(lines)}, lines, skew

    def _line(self, source: NewsSource, fetch: FeedFetch, item: NewsItem, record: dict, previous: str | None,
              skew: float | None) -> dict:  # fmt: skip
        feed = source.feed
        return {"line": ITEM_LINE, **record, "publisher": feed.publisher, "feed": feed.id, "url": item.url,
                "title": item.title, "summary": item.summary, "published_raw": item.published.raw,
                "published_at": item.published.value, "published_precision": item.published.precision,
                "first_seen_at": fetch.received_at.isoformat(), "previous_poll_at": previous,
                "server_date": fetch.server_date.isoformat() if fetch.server_date else None,
                "clock_skew_s": skew, "run_id": self.run_id}  # fmt: skip

    def _check_times(self, source: NewsSource, items: list[NewsItem]) -> None:
        if items and all(item.published.value is None for item in items):
            self.episodes.fail(source.feed.id, NO_TIMES, f"{source.feed.id}: no item time could be read")
        elif items:
            self.episodes.ok(source.feed.id, (NO_TIMES,))

    def _check_window(self, source: NewsSource, records: list[dict]) -> None:
        if any(r["beyond_window"] for r in records):
            self.episodes.fail(source.feed.id, BEYOND_WINDOW, f"{source.feed.id}: lists items older than 13 days")
        elif records:
            self.episodes.ok(source.feed.id, (BEYOND_WINDOW,))

    def _check_stale(self, source: NewsSource, now: datetime) -> None:
        feed = source.feed
        last_new = self.memory.last_new.get(feed.id)
        if last_new is None:
            return  # nothing new seen yet: its first new item starts the clock
        if self.stale.is_stale(feed, datetime.fromisoformat(last_new), now):
            self.episodes.fail(feed.id, STALE, f"{feed.id}: nothing new since {last_new[:16]}")
        else:
            self.episodes.ok(feed.id, (STALE,))


def _matched(items: list[NewsItem], records: list[dict]) -> list[tuple[NewsItem, dict]]:
    """Pairs each stored record with its item (records come back in item order, skipping known ones)."""
    by_key = {(item_id(i.url), version_of(i.title, i.summary, i.published.raw)): i for i in items}
    return [(by_key[(r["item_id"], r["version"])], r) for r in records]


def _skew(fetch: FeedFetch) -> float | None:
    if fetch.server_date is None or fetch.server_date.tzinfo is None:
        return None
    return round((fetch.received_at - fetch.server_date).total_seconds(), 1)
