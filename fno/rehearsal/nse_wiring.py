"""NSE's archive in a rehearsal (story REH1b), chosen by `build_nse_source`: every file the record does not already
hold in Drive is "not recorded". The rehearsal's session never sends a request; it fails at once as a request that
could never be sent, so the library's own rule applies (no retry, no wait, nothing archived) and the step's line says
why. A file Drive already holds is read from Drive as in a real run."""

from __future__ import annotations

import os
from collections.abc import Mapping

import requests

from .mode import rehearsal

NOT_RECORDED = "rehearsal:NOT_RECORDED {url}: not in the record, and a rehearsal never fetches"


class NotRecorded(requests.exceptions.InvalidURL):
    """A rehearsal's request to a live source: never sent (the record did not hold the file)."""


class NotRecordedSession:
    def __init__(self):
        self.headers: dict[str, str] = {}

    def get(self, url, *args, **kwargs):
        raise NotRecorded(NOT_RECORDED.format(url=url))

    def head(self, url, *args, **kwargs):
        raise NotRecorded(NOT_RECORDED.format(url=url))


def rehearsed_session(session, env: Mapping[str, str] = os.environ):
    return session if rehearsal(env) is None else NotRecordedSession()
