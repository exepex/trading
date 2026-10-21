"""NSE's day list of corporate announcements, fetched once per mark (story A21 part 2): one GET with a hard 5 s
timeout and no retry, on a paced session with `PublicData`'s headers, through A12's own URL template (imported, never
copied). Everything it can raise becomes a named `PollFailed`; NSE calls sit outside A9b's retry policy
(`docs/DATA_SOURCES.md`)."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

import requests

from ..filings.sources import NseAnnouncementsSource
from ..http_pacing import PacedSession
from ..providers.public import HEADERS
from .constants import REQUEST_TIMEOUT


class PollFailed(RuntimeError):
    def __init__(self, kind: str):
        super().__init__(kind)
        self.kind = kind  # refused_403, refused_429, refused_<status>, timeout, unreachable, bad_json


@dataclass(frozen=True)
class DayList:
    items: list[dict]
    raw: bytes
    arrived_at: datetime  # the response's arrival: the first-seen time (judge 355 addendum 1)


class AnnouncementSource(Protocol):
    def day_list(self, day: date) -> DayList: ...


class NseDayList:
    def __init__(self, clock: Callable[[], datetime], session: requests.Session | None = None):
        self.clock = clock
        self.session = session or PacedSession()
        self.session.headers.update(HEADERS)

    def day_list(self, day: date) -> DayList:
        url = NseAnnouncementsSource.API.format(day=f"{day:%d-%m-%Y}")
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        except requests.Timeout as error:
            raise PollFailed("timeout") from error
        except requests.RequestException as error:
            raise PollFailed("unreachable") from error
        arrived = self.clock()
        if response.status_code != 200:
            raise PollFailed(f"refused_{response.status_code}")
        try:
            items = json.loads(response.content)
        except ValueError as error:
            raise PollFailed("bad_json") from error
        if not isinstance(items, list):
            raise PollFailed("bad_json")
        return DayList(items, response.content, arrived)
