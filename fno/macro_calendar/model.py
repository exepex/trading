"""A release date as a publisher's calendar lists it, and the row A20c keeps for it."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

INDIA_CPI, INDIA_IIP, INDIA_GDP = "india_cpi", "india_iip", "india_gdp"
US_FOMC, US_CPI, US_PAYROLLS = "us_fomc", "us_cpi", "us_payrolls"
MOSPI, FED, BLS = "mospi", "fed", "bls"
COLUMNS = ("kind", "date", "planned", "source", "source_url", "seen_at", "period_start", "period_end")


class CalendarFailed(RuntimeError):
    """A publisher's calendar could not be read whole (refused, unreachable, not in its layout, the wrong number of
    dates): never "no dates"."""


@dataclass(frozen=True)
class ReleaseDate:
    kind: str
    day: date  # the expected release day (a planned weekend date moves to the Monday: MOSPI's footnote)
    source_url: str  # the calendar document the date was read from
    planned: date | None = None  # the date as printed, when it differs from `day`

    def row(self, source: str, seen_at: str, period: tuple[date, date]) -> dict:
        return {"kind": self.kind, "date": self.day.isoformat(), "planned": (self.planned or self.day).isoformat(),
                "source": source, "source_url": self.source_url, "seen_at": seen_at,
                "period_start": period[0].isoformat(), "period_end": period[1].isoformat()}  # fmt: skip


@dataclass(frozen=True)
class Calendar:
    dates: tuple[ReleaseDate, ...]
    document: bytes  # the publisher's file as fetched, kept write-once in Drive
    extension: str
    period: tuple[date, date]  # first and last day the document covers: only a date inside it can be withdrawn
