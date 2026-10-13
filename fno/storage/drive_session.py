"""Talks to the Google Drive API for every Drive store: signs in again once when the access token expires and retries
Google's temporary failures after growing waits. Knows nothing about folders or files."""

from __future__ import annotations

import time
from collections.abc import Callable

import requests

TIMEOUT_SECONDS = 60
UNAUTHORIZED = 401  # the access token expired: sign in again once
TRANSIENT = frozenset({429, 500, 502, 503, 504})  # Google's temporary answers: wait and try again
RETRY_WAITS = (2, 8, 30, 60)  # seconds before each retry of a temporary failure


class DriveSession:
    def __init__(
        self,
        token: Callable[[], str],
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        """`token` returns a fresh access token; it is asked again when Drive answers 401 (tokens last about an
        hour, so a long run would otherwise fail midway)."""
        self.token, self.sleep = token, sleep
        self.session = session or requests.Session()
        self._sign_in()

    def _sign_in(self) -> None:
        self.session.headers["Authorization"] = f"Bearer {self.token()}"

    def request(self, method: str, url: str, accept: frozenset[int] = frozenset(), **kwargs) -> requests.Response:
        """A call that signs in again once when the token has expired and retries temporary failures (429, 5xx,
        dropped connections) after growing waits. Statuses in `accept` are returned as answers; any other error, or
        the last temporary failure, is raised."""
        send = getattr(self.session, method)
        signed_in_again = False
        for wait in (*RETRY_WAITS, None):
            try:
                response = send(url, timeout=TIMEOUT_SECONDS, **kwargs)
            except requests.ConnectionError:
                if wait is None:
                    raise
                self.sleep(wait)
                continue
            status = getattr(response, "status_code", None)
            if status == UNAUTHORIZED and not signed_in_again:
                self._sign_in()
                signed_in_again = True
                response = send(url, timeout=TIMEOUT_SECONDS, **kwargs)
                status = getattr(response, "status_code", None)
            if status in TRANSIENT and wait is not None:
                self.sleep(wait)
                continue
            if status not in accept:
                response.raise_for_status()
            return response
        raise AssertionError("unreachable")

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request("get", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self.request("post", url, **kwargs)
