"""What the poller has already stored (story A19, scope 6): item ids and their versions, headlines of the last 24
hours, and each feed's last successful poll and last new item. It is kept for `SEEN_WINDOW` (14 days, about 2.5
times the longest feed span measured: Mint Economy, 5.7 days), saved as a snapshot and restored after a restart, so
a feed that still lists an old item never makes it look new with a late first-seen time."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from ..models import IST
from .identity import headline_key, item_id, version_of
from .names import DAY, FAILED, POLL_LINE
from .parse import NewsItem
from .settings import Feed

SEEN_WINDOW = timedelta(days=14)
BEYOND_WINDOW_AGE = timedelta(days=13)  # one day of margin inside the window
HEADLINE_LINK = timedelta(hours=24)
JUST_SEEN = timedelta(minutes=5)  # one poll: an item stored by one feed credits every feed listing it in that poll
FIELDS = ("versions", "first_seen", "headlines", "last_poll", "last_new", "last_heartbeat")


@dataclass
class SeenMemory:
    versions: dict[str, list[str]] = field(default_factory=dict)  # item id -> versions stored
    first_seen: dict[str, str] = field(default_factory=dict)  # item id -> first first_seen_at
    headlines: dict[str, list[str]] = field(default_factory=dict)  # key -> [item id, publisher, first_seen_at]
    last_poll: dict[str, str] = field(default_factory=dict)  # feed id -> last successful poll
    last_new: dict[str, str] = field(default_factory=dict)  # feed id -> last new item or version
    last_heartbeat: str | None = None  # the last poll of any feed

    def observe(self, feed: Feed, items: list[NewsItem], seen_at: datetime, first_poll: bool) -> list[dict]:
        """Records the feed's unseen items and versions; returns their identity fields. `first_poll`: the feed was
        never polled before, so what it lists was published earlier and is only first seen now (`bootstrap`)."""
        stored = [record for item in items if (record := self._observe(feed, item, seen_at, first_poll))]
        if stored or any(self._just_seen(item_id(item.url), seen_at) for item in items):
            self.last_new[feed.id] = seen_at.isoformat()  # a feed listing an item another feed stored now is alive
        return stored

    def mark_poll(self, feed: Feed, polled_at: datetime) -> str | None:
        """Notes a successful poll; returns the feed's previous one (None for its first poll ever)."""
        previous = self.last_poll.get(feed.id)
        self.last_poll[feed.id] = polled_at.isoformat()
        return previous

    def _observe(self, feed: Feed, item: NewsItem, seen_at: datetime, first_poll: bool) -> dict | None:
        key, version = item_id(item.url), version_of(item.title, item.summary, item.published.raw)
        known = self.versions.get(key)
        if known is not None and version in known:
            return None
        record = {"item_id": key, "version": version, "new_item": known is None,
                  "same_headline_as": None, "beyond_window": False, "bootstrap": first_poll}  # fmt: skip
        if known is None:
            record["same_headline_as"] = self._link_headline(key, item.title, feed.publisher, seen_at)
            record["beyond_window"] = not first_poll and _published_before(item, seen_at - BEYOND_WINDOW_AGE)
            self.first_seen[key] = seen_at.isoformat()
        self.versions.setdefault(key, []).append(version)
        return record

    def _just_seen(self, key: str, seen_at: datetime) -> bool:
        first = self.first_seen.get(key)
        return first is not None and seen_at - datetime.fromisoformat(first) <= JUST_SEEN

    def _link_headline(self, key: str, title: str, publisher: str, seen_at: datetime) -> str | None:
        words = headline_key(title)
        if not words:
            return None
        earlier = self.headlines.get(words)
        linked = None
        if earlier and earlier[1] != publisher and seen_at - datetime.fromisoformat(earlier[2]) <= HEADLINE_LINK:
            linked = earlier[0]
        if earlier is None or linked is None:
            self.headlines[words] = [key, publisher, seen_at.isoformat()]
        return linked

    def replay(self, line: dict) -> None:
        """Applies one stored part line (scope 4) through the same updates the live poll made, so a memory rebuilt
        after a restart equals the live one."""
        if line["line"] == POLL_LINE:
            self.last_heartbeat = line["polled_at"]
            for feed_id, outcome in line["feeds"].items():
                if not outcome["outcome"].startswith(FAILED):
                    seen = outcome.get("seen_at", line["polled_at"])
                    self.last_poll[feed_id] = seen
                    self.last_new.setdefault(feed_id, seen)
            return
        key, seen = line["item_id"], line["first_seen_at"]
        if line["new_item"] and key not in self.versions:
            self._link_headline(key, line["title"], line["publisher"], datetime.fromisoformat(seen))
            self.first_seen[key] = seen
        if line["version"] not in self.versions.setdefault(key, []):
            self.versions[key].append(line["version"])
        self.last_new[line["feed"]] = max(self.last_new.get(line["feed"], seen), seen)

    def prune(self, now: datetime) -> None:
        """Forgets items first seen before the window and headlines older than 24 hours."""
        old = {key for key, seen in self.first_seen.items() if datetime.fromisoformat(seen) < now - SEEN_WINDOW}
        for key in old:
            self.first_seen.pop(key)
            self.versions.pop(key, None)
        self.headlines = {k: v for k, v in self.headlines.items()
                          if now - datetime.fromisoformat(v[2]) <= HEADLINE_LINK}  # fmt: skip

    def to_dict(self) -> dict:
        return {name: getattr(self, name) for name in FIELDS}

    @classmethod
    def from_dict(cls, data: dict) -> SeenMemory:
        return cls(**{name: data[name] for name in FIELDS})


def _published_before(item: NewsItem, limit: datetime) -> bool:
    value = item.published.value
    if value is None:
        return False
    if item.published.precision == DAY:
        return date.fromisoformat(value) < limit.astimezone(IST).date()  # a date-only time is an IST date
    return datetime.fromisoformat(value) < limit
