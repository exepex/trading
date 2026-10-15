"""The host clock checked against independent servers on every run (design 4.4's clock contract): GitHub's and
Slack's HTTP `Date` headers. A skew above 5 s is a WARNING; no answer at all is recorded as unchecked, never ignored.
The `Date` header has one-second resolution, so a measured skew is good to about one second."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

import requests

from ..models import now_ist

GITHUB_TIME_URL = "https://api.github.com"
SLACK_TIME_URL = "https://slack.com/api/api.test"  # answers without a token; nothing is posted
TIME_REQUEST_TIMEOUT_SECONDS = 5
SKEW_LIMIT_SECONDS = 5
CLOCK_OK, CLOCK_SKEW, CLOCK_UNCHECKED = "clock_ok", "clock_skew", "clock_unchecked"
WARNING_LINE = "WARNING: host clock differs from {server} by {skew:+.1f} s (limit {limit} s)"


class ServerClock(ABC):
    name: str

    @abstractmethod
    def skew_seconds(self) -> float | None:
        """Host clock minus the server's clock, in seconds; None when the server gave no time."""


class HttpDateClock(ServerClock):
    def __init__(self, name: str, url: str, now: Callable[[], datetime] = now_ist, session=None):
        self.name, self.url, self.now = name, url, now
        self.session = session or requests.Session()

    def skew_seconds(self) -> float | None:
        sent = self.now()
        try:
            response = self.session.head(self.url, timeout=TIME_REQUEST_TIMEOUT_SECONDS)
            server = parsedate_to_datetime(response.headers["Date"])
        except (requests.RequestException, KeyError, TypeError, ValueError):
            return None
        middle = sent + (self.now() - sent) / 2
        return (middle - (server + timedelta(seconds=0.5))).total_seconds()  # the header drops the fraction


@dataclass(frozen=True)
class ClockReading:
    status: str
    skews: dict[str, float]  # server name -> host minus server, seconds (servers that answered)

    @property
    def worst(self) -> float | None:
        return max(self.skews.values(), key=abs) if self.skews else None

    def warning(self) -> str:
        """The WARNING line to print, or empty."""
        if self.status != CLOCK_SKEW:
            return ""
        server = max(self.skews, key=lambda name: abs(self.skews[name]))
        return WARNING_LINE.format(server=server, skew=self.skews[server], limit=SKEW_LIMIT_SECONDS)


class ClockCheck:
    def __init__(self, servers: list[ServerClock]):
        self.servers = servers

    def check(self) -> ClockReading:
        skews = {s.name: skew for s in self.servers if (skew := s.skew_seconds()) is not None}
        if not skews:
            return ClockReading(CLOCK_UNCHECKED, {})
        too_far = any(abs(skew) > SKEW_LIMIT_SECONDS for skew in skews.values())
        return ClockReading(CLOCK_SKEW if too_far else CLOCK_OK, skews)
