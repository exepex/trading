"""Sends one alert line to the owner. The Slack sender posts only to #fno-desk with `FNO_SLACK_BOT_TOKEN` (never the
market-brief tool's `SLACK_*` variables); without the token nothing is sent and the caller is told so."""

from __future__ import annotations

from abc import ABC, abstractmethod

import requests

SLACK_POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"
SLACK_TIMEOUT_SECONDS = 15
SENT = "alert sent to #fno-desk"
NOT_SENT = "alert NOT sent: {reason}"
NO_TOKEN = "FNO_SLACK_BOT_TOKEN is not set"


class AlertSender(ABC):
    @abstractmethod
    def send(self, text: str) -> str:
        """Send the alert; returns a one-line outcome to print (never raises, never prints a credential)."""


class SlackChannelAlerts(AlertSender):
    def __init__(self, token: str, channel: str, session: requests.Session | None = None):
        self._token = token
        self._channel = channel
        self._session = session or requests.Session()

    def send(self, text: str) -> str:
        try:
            response = self._session.post(
                SLACK_POST_MESSAGE_URL,
                headers={"Authorization": f"Bearer {self._token}"},
                json={"channel": self._channel, "text": text},
                timeout=SLACK_TIMEOUT_SECONDS,
            )
            body = response.json()
        except (requests.RequestException, ValueError) as error:
            return NOT_SENT.format(reason=type(error).__name__)
        return SENT if body.get("ok") else NOT_SENT.format(reason=body.get("error", f"HTTP {response.status_code}"))


class NoAlertSender(AlertSender):
    """Used when no Slack token is set: says so instead of failing silently."""

    def __init__(self, reason: str = NO_TOKEN):
        self._reason = reason

    def send(self, text: str) -> str:
        return NOT_SENT.format(reason=self._reason)
