"""RBI's pages over HTTP (story A21): one GET with a hard timeout and one retry; any failure becomes a named
`RateFetchError` (refused with its status, or unreachable), never an unhandled exception."""

from __future__ import annotations

from typing import Protocol

import requests

from .constants import TIMEOUT_SECONDS

HEADERS = {"User-Agent": "Mozilla/5.0 (Omenix F&O research; rates capture)", "Accept": "text/html"}
TRIES = 2


class RateFetchError(RuntimeError):
    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind  # "refused" or "unreachable"


class PageFetcher(Protocol):
    def get(self, url: str) -> bytes: ...


class RbiPages:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)

    def get(self, url: str) -> bytes:
        problem = RateFetchError("unreachable", f"{url}: no answer")
        for _ in range(TRIES):
            try:
                response = self.session.get(url, timeout=TIMEOUT_SECONDS)
            except requests.RequestException as error:
                problem = RateFetchError("unreachable", f"{url}: {type(error).__name__}")
                continue
            if response.status_code == 200 and response.content.strip():
                return response.content
            problem = RateFetchError("refused", f"{url}: HTTP {response.status_code}")
        raise problem
