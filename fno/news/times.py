"""Published-time formats (story A19, scope 2): one strategy per way a feed writes `pubDate`, each stating its
precision. A date-only time stays a date (`2026-10-16`, precision `day`), never an invented midnight; a time that
cannot be read stays `None` with the feed's raw text kept beside it."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

from ..models import IST
from .names import DAY, SECOND


@dataclass(frozen=True)
class PublishedTime:
    raw: str
    value: str | None  # UTC ISO 8601 for `second`, an ISO date for `day`, None when unreadable
    precision: str | None


class PublishedTimeFormat(ABC):
    name: str = ""

    @abstractmethod
    def read(self, raw: str) -> PublishedTime:
        """Never raises: an unreadable time is `PublishedTime(raw, None, None)`."""


class Rfc822Time(PublishedTimeFormat):
    """`Fri, 16 Oct 2026 15:08:49 +0530` or `... GMT` (ET, Mint, BusinessLine)."""

    name = "rfc822"

    def read(self, raw: str) -> PublishedTime:
        moment = _rfc822(raw)
        if moment is None or moment.tzinfo is None:
            return PublishedTime(raw, None, None)
        return PublishedTime(raw, moment.astimezone(UTC).isoformat(), SECOND)


class IstWithoutZoneTime(PublishedTimeFormat):
    """`Fri, 16 Oct 2026 15:00:00` with no zone: RBI publishes India time."""

    name = "rfc822_ist"

    def read(self, raw: str) -> PublishedTime:
        moment = _rfc822(raw)
        if moment is None or moment.tzinfo is not None:
            return PublishedTime(raw, None, None)
        return PublishedTime(raw, moment.replace(tzinfo=IST).astimezone(UTC).isoformat(), SECOND)


class DayOnlyTime(PublishedTimeFormat):
    """`16 Oct, 2026 +0530` (SEBI): a date, kept as a date."""

    name = "day_comma_year"

    def read(self, raw: str) -> PublishedTime:
        try:
            day = datetime.strptime(raw.strip(), "%d %b, %Y %z").date()
        except ValueError:
            return PublishedTime(raw, None, None)
        return PublishedTime(raw, day.isoformat(), DAY)


def _rfc822(raw: str) -> datetime | None:
    try:
        return parsedate_to_datetime(raw.strip())
    except (TypeError, ValueError, IndexError):
        return None


TIME_FORMATS: dict[str, PublishedTimeFormat] = {f.name: f for f in (Rfc822Time(), IstWithoutZoneTime(), DayOnlyTime())}
