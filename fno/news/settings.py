"""The `news` settings of config.yaml (story A19, scope 2): the feeds, the publisher switch, the polling window and
the overnight bridge. Every value is checked here, so a typo stops the run with a named line instead of a silent
default."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from .names import OFFICIAL, PUBLISHER

FEED_KINDS = (PUBLISHER, OFFICIAL)
REQUIRED_FEED_KEYS = ("id", "publisher", "kind", "url", "time_format", "stale_session_hours", "stale_any_hours")
BAD = "news settings: {what}"


class NewsSettingsError(ValueError):
    pass


@dataclass(frozen=True)
class Feed:
    id: str
    publisher: str
    kind: str
    url: str
    time_format: str
    stale_session_hours: float
    stale_any_hours: float
    excluded_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class Window:
    """IST clock times; `start == end` means all day."""

    start: time
    end: time

    @property
    def all_day(self) -> bool:
        return self.start == self.end


@dataclass(frozen=True)
class NewsSettings:
    feeds: tuple[Feed, ...]
    publisher_feeds: bool
    window: Window
    overnight_bridge: bool

    def active_feeds(self) -> tuple[Feed, ...]:
        """The feeds to read: every feed, or only the official ones when the publisher switch is off."""
        return tuple(f for f in self.feeds if self.publisher_feeds or f.kind != PUBLISHER)


def news_settings(cfg: dict, formats: frozenset[str]) -> NewsSettings:
    """`cfg`: the whole app config; `formats`: the time-format names the parser knows."""
    news = cfg.get("news")
    if not isinstance(news, dict):
        raise NewsSettingsError(BAD.format(what="config.yaml has no `news` section"))
    feeds = tuple(_feed(raw, formats) for raw in news.get("feeds") or [])
    if not feeds:
        raise NewsSettingsError(BAD.format(what="no feeds listed"))
    ids = [f.id for f in feeds]
    if len(set(ids)) != len(ids):
        raise NewsSettingsError(BAD.format(what="a feed id is listed twice"))
    window = news.get("active_window") or {}
    return NewsSettings(
        feeds,
        _flag(news, "publisher_feeds"),
        Window(_clock(window.get("start"), "active_window.start"), _clock(window.get("end"), "active_window.end")),
        _flag(news, "overnight_bridge"),
    )


def _feed(raw, formats: frozenset[str]) -> Feed:
    if not isinstance(raw, dict) or any(key not in raw for key in REQUIRED_FEED_KEYS):
        raise NewsSettingsError(BAD.format(what=f"a feed needs {', '.join(REQUIRED_FEED_KEYS)}"))
    if raw["kind"] not in FEED_KINDS:
        raise NewsSettingsError(BAD.format(what=f"feed {raw['id']}: kind must be one of {FEED_KINDS}"))
    if raw["time_format"] not in formats:
        raise NewsSettingsError(BAD.format(what=f"feed {raw['id']}: unknown time_format {raw['time_format']!r}"))
    if not str(raw["url"]).startswith("https://"):
        raise NewsSettingsError(BAD.format(what=f"feed {raw['id']}: the url must be https"))
    limits = [_hours(raw, key) for key in ("stale_session_hours", "stale_any_hours")]
    return Feed(str(raw["id"]), str(raw["publisher"]), raw["kind"], str(raw["url"]), raw["time_format"], *limits,
                tuple(raw.get("excluded_paths") or ()))  # fmt: skip


def _hours(raw: dict, key: str) -> float:
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
        raise NewsSettingsError(BAD.format(what=f"feed {raw['id']}: {key} must be a positive number of hours"))
    return float(value)


def _flag(news: dict, key: str) -> bool:
    value = news.get(key)
    if not isinstance(value, bool):
        raise NewsSettingsError(BAD.format(what=f"{key} must be true or false"))
    return value


def _clock(value, key: str) -> time:
    try:
        return time.fromisoformat(str(value))
    except ValueError as exc:
        raise NewsSettingsError(BAD.format(what=f"{key} must be an IST clock time like 07:00")) from exc
