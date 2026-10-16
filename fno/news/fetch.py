"""Where a feed's answer comes from (story A19, scope 1): the `NewsSource` port and its RSS adapter. One request per
feed per poll, paced per host (`fno/http_pacing.py`); the next poll, 5 minutes later, is the retry. The adapter
remembers the feed's `ETag` and `Last-Modified`, so an unchanged feed costs one short `304` answer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime

import requests

from ..http_pacing import PacedSession
from .names import HTTP_ERROR
from .parse import FeedProblem
from .settings import Feed

USER_AGENT = "OmenixResearch/1.0 (personal research; RSS reader)"
TIMEOUT_SECONDS = 30
NOT_MODIFIED_STATUS = 304


@dataclass(frozen=True)
class FeedFetch:
    status: int
    data: bytes
    server_date: datetime | None  # the answer's `Date` header (the clock check, scope 8); None from a cache
    requested_at: datetime
    received_at: datetime

    @property
    def not_modified(self) -> bool:
        return self.status == NOT_MODIFIED_STATUS


class NewsSource(ABC):
    feed: Feed

    @abstractmethod
    def fetch(self) -> FeedFetch:
        """The feed's current answer; FeedProblem(HTTP_ERROR) when there is none (never another exception)."""


class RssFeedSource(NewsSource):
    def __init__(self, feed: Feed, clock: Callable[[], datetime], session: requests.Session | None = None):
        self.feed, self.clock = feed, clock
        self.session = session or PacedSession()
        self._validators: dict[str, str] = {}

    def fetch(self) -> FeedFetch:
        requested_at = self.clock()
        try:
            response = self.session.get(self.feed.url, headers=self._headers(), timeout=TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            raise FeedProblem(HTTP_ERROR, f"no answer ({type(exc).__name__})") from exc
        received_at = self.clock()
        if response.status_code != NOT_MODIFIED_STATUS and not 200 <= response.status_code < 300:
            raise FeedProblem(HTTP_ERROR, f"HTTP {response.status_code}")
        self._remember(response)
        served_by_cache = str(response.headers.get("Age", "0")).strip() not in ("", "0")
        server_date = None if served_by_cache else _date(response.headers.get("Date"))
        return FeedFetch(response.status_code, response.content, server_date, requested_at, received_at)

    def _headers(self) -> dict[str, str]:
        headers = {"User-Agent": USER_AGENT}
        if "etag" in self._validators:
            headers["If-None-Match"] = self._validators["etag"]
        if "last_modified" in self._validators:
            headers["If-Modified-Since"] = self._validators["last_modified"]
        return headers

    def _remember(self, response) -> None:
        for header, key in (("ETag", "etag"), ("Last-Modified", "last_modified")):
            if response.headers.get(header):
                self._validators[key] = response.headers[header]


def _date(header: str | None) -> datetime | None:
    if not header:
        return None
    try:
        return parsedate_to_datetime(header)
    except (TypeError, ValueError, IndexError):
        return None
