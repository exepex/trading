"""Posting the card (story T1): `CardPoster` returns Slack's own server timestamp of the post (`ts`), the card's
issuance time (design 04 section 4.4), or why it was not sent. Only #fno-desk with `FNO_SLACK_BOT_TOKEN`. A failed post
is retried once; the outcome line uses the alert sender's wording ("alert NOT sent: <reason>"), never the token."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import requests

from ..alerts.sender import NO_TOKEN, NOT_SENT, SENT, slack_post

ATTEMPTS = 2  # the post and one retry (design 4.1: "a failed post is retried and logged")
RETRY_PAUSE_SECONDS = 5.0


@dataclass(frozen=True)
class PostReceipt:
    outcome: str  # the line to print
    ts: str | None = None  # Slack's message timestamp, set only when Slack accepted the post
    channel: str | None = None

    @property
    def sent(self) -> bool:
        return self.ts is not None

    @property
    def server_time(self) -> datetime | None:
        """Slack's server time of the post (its `ts` is seconds since 1970, UTC)."""
        return datetime.fromtimestamp(float(self.ts), UTC) if self.ts else None


class CardPoster(ABC):
    @abstractmethod
    def post(self, text: str) -> PostReceipt:
        """Post the card; never raises."""


class SlackCardPoster(CardPoster):
    def __init__(self, token: str, channel: str, session: requests.Session | None = None, sleep: Callable = time.sleep):
        self._token, self._channel = token, channel
        self._session, self._sleep = session or requests.Session(), sleep

    def post(self, text: str) -> PostReceipt:
        failure = None
        for attempt in range(ATTEMPTS):
            if attempt:
                self._sleep(RETRY_PAUSE_SECONDS)
            body, failure = slack_post(self._session, self._token, self._channel, text)
            if failure is None and body.get("ts"):
                return PostReceipt(SENT, str(body["ts"]), body.get("channel", self._channel))
            failure = failure or "no ts in Slack's answer"
        return PostReceipt(NOT_SENT.format(reason=f"{failure} after {ATTEMPTS} attempts"))


class NoCardPoster(CardPoster):
    """Used when no Slack token is set: says so instead of failing silently."""

    def __init__(self, reason: str = NO_TOKEN):
        self._reason = reason

    def post(self, text: str) -> PostReceipt:
        return PostReceipt(NOT_SENT.format(reason=self._reason))
