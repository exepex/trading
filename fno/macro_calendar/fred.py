"""US CPI and payrolls release dates from FRED (St. Louis Fed) release-dates API (story A20c; owner's free key, 16 Oct
2026, GitHub secret FNO_FRED_API_KEY). BLS itself refuses GitHub's runners (probe run 38900266338). FRED lists each
release's scheduled dates when asked to include dates with no data yet. The key travels in the query, so no message
ever names the URL with its query: a failure says the release and the reason only."""

from __future__ import annotations

from datetime import date

import requests

from .http import TIMEOUT_SECONDS
from .model import US_CPI, US_PAYROLLS, Calendar, CalendarFailed, ReleaseDate

URL = "https://api.stlouisfed.org/fred/release/dates"
RELEASES = {US_CPI: 10, US_PAYROLLS: 50}  # Consumer Price Index; Employment Situation
SOURCE_URL = "https://fred.stlouisfed.org/releases/{release_id}"  # the public page named in each row (no key)
LATEST = 40  # the newest 40 dates of each release: over a year of monthly releases, past and scheduled
FAILED = "FRED release {release_id} ({kind}): {reason}"


class FredReleaseCalendar:
    source = "fred"

    def __init__(self, session: requests.Session, api_key: str):
        self.session, self.api_key = session, api_key

    def fetch(self, today: date) -> Calendar:
        dates, documents = [], []
        for kind, release_id in RELEASES.items():
            days, raw = self._release(kind, release_id, today)
            dates += [ReleaseDate(kind, day, SOURCE_URL.format(release_id=release_id)) for day in days]
            documents.append(raw)
        last = max(d.day for d in dates)
        return Calendar(tuple(sorted(dates, key=lambda d: (d.day, d.kind))), b"\n".join(documents), "json",
                        (date(today.year, 1, 1), last))  # fmt: skip

    def _release(self, kind: str, release_id: int, today: date) -> tuple[list[date], bytes]:
        params = {"release_id": release_id, "api_key": self.api_key, "file_type": "json", "sort_order": "desc",
                  "limit": LATEST, "include_release_dates_with_no_data": "true"}  # fmt: skip
        try:
            response = self.session.get(URL, params=params, timeout=TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            raise CalendarFailed(FAILED.format(release_id=release_id, kind=kind, reason=type(exc).__name__)) from None
        if response.status_code != 200:
            reason = f"HTTP {response.status_code}"
            raise CalendarFailed(FAILED.format(release_id=release_id, kind=kind, reason=reason))
        try:
            rows = response.json()["release_dates"]
            days = sorted({date.fromisoformat(row["date"]) for row in rows if row["release_id"] == release_id})
        except (ValueError, KeyError, TypeError) as exc:
            reason = f"not FRED's release-dates answer ({type(exc).__name__})"
            raise CalendarFailed(FAILED.format(release_id=release_id, kind=kind, reason=reason)) from None
        days = [day for day in days if day.year >= today.year]
        if not any(day > today for day in days):
            reason = "no scheduled date after today"
            raise CalendarFailed(FAILED.format(release_id=release_id, kind=kind, reason=reason))
        return days, response.content.replace(self.api_key.encode(), b"<key>") if self.api_key else response.content
