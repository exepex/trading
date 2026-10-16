"""One GET for the calendar adapters: the answer, or CalendarFailed naming the URL (never a raw HTTP error)."""

from __future__ import annotations

import requests

from .model import CalendarFailed

TIMEOUT_SECONDS = 60


def get_ok(session: requests.Session, url: str) -> requests.Response:
    try:
        response = session.get(url, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise CalendarFailed(f"{url}: {type(exc).__name__}") from exc
    if response.status_code != 200:
        raise CalendarFailed(f"{url}: HTTP {response.status_code}")
    return response
