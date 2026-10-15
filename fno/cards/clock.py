"""The clock contract of design 04 section 4.4 (story T1 criterion 7): times are stored in UTC with their offset and
shown in IST, and the host clock is checked against Slack's and GitHub's server times on every posting run. A server
time outside the host's before-and-after window by more than 5 seconds (plus the server clock's resolution) is a
WARNING. `ServerClock` is the interface; `HttpDateClock` reads a server's HTTP `Date` header (one-second resolution)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import requests

from ..constants import CLOCK_SKEW_WARNING_SECONDS

TIMEOUT_SECONDS = 15
OK_LINE = "clock: host vs {server} within {skew:.1f} s"
WARNING_LINE = "clock WARNING: host vs {server} off by {skew:.1f} s (limit {limit:.0f} s)"
UNCHECKED_LINE = "clock: host vs {server} not checked ({why})"


class ServerTimeUnknown(RuntimeError):
    """The server's time could not be read; the message says why (never a credential)."""


class ServerClock(ABC):
    name: str = "server"
    resolution_seconds: float = 0.0

    @abstractmethod
    def now(self) -> datetime:
        """The server's current time (aware), or ServerTimeUnknown."""


class HttpDateClock(ServerClock):
    resolution_seconds = 1.0

    def __init__(self, name: str, url: str, head: Callable | None = None):
        self.name, self.url, self._head = name, url, head or requests.head

    def now(self) -> datetime:
        try:
            response = self._head(self.url, timeout=TIMEOUT_SECONDS)
            moment = parsedate_to_datetime(response.headers["Date"])
            return moment if moment.tzinfo else moment.replace(tzinfo=UTC)  # "-0000" is UTC (RFC 5322)
        except (requests.RequestException, KeyError, TypeError, ValueError) as error:
            raise ServerTimeUnknown(type(error).__name__) from None


@dataclass(frozen=True)
class SkewCheck:
    server: str
    skew_seconds: float | None  # None: not checked
    warning: bool
    line: str

    def stored(self) -> dict:
        """Kept with its line, so an unchecked server says why in the record too (not only on screen)."""
        return {"server": self.server, "skew_seconds": self.skew_seconds, "warning": self.warning, "line": self.line}


def skew_check(
    server: str, server_time: datetime, before: datetime, after: datetime, resolution: float = 0.0
) -> SkewCheck:
    """How far the server's time falls outside the host's [before, after] window (0 inside it)."""
    early = (before - server_time).total_seconds() - resolution
    late = (server_time - after).total_seconds() - resolution
    skew = max(0.0, early, late)
    if skew > CLOCK_SKEW_WARNING_SECONDS:
        return SkewCheck(
            server, skew, True, WARNING_LINE.format(server=server, skew=skew, limit=CLOCK_SKEW_WARNING_SECONDS)
        )
    return SkewCheck(server, skew, False, OK_LINE.format(server=server, skew=skew))


def unchecked(server: str, why: str) -> SkewCheck:
    return SkewCheck(server, None, False, UNCHECKED_LINE.format(server=server, why=why))


def check_server(clock: ServerClock, host_now: Callable[[], datetime]) -> SkewCheck:
    before = host_now()
    try:
        server_time = clock.now()
    except ServerTimeUnknown as error:
        return unchecked(clock.name, str(error))
    return skew_check(clock.name, server_time, before, host_now(), clock.resolution_seconds)


def utc_text(moment: datetime) -> str:
    """A stored time: UTC with its offset (`+00:00`)."""
    return moment.astimezone(UTC).isoformat()
