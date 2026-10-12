"""Alert sender (used by O5's refused-commit alert): posts to #fno-desk with the bot token, never raises, never prints
the token, and says plainly when nothing was sent."""

import requests

from fno import composition
from fno.alerts.sender import SLACK_POST_MESSAGE_URL, NoAlertSender, SlackChannelAlerts
from fno.constants import ENV_FNO_SLACK_BOT_TOKEN, FNO_DESK_CHANNEL_ID

TOKEN = "test-token-not-real"


class FakeResponse:
    def __init__(self, body, status=200):
        self._body, self.status_code = body, status

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, body=None, error=None):
        self.calls, self._body, self._error = [], body, error

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self._error:
            raise self._error
        return FakeResponse(self._body)


def test_posts_the_text_to_the_channel_with_the_bot_token():
    session = FakeSession({"ok": True})
    assert SlackChannelAlerts(TOKEN, FNO_DESK_CHANNEL_ID, session).send("refused") == "alert sent to #fno-desk"
    ((url, kwargs),) = session.calls
    assert url == SLACK_POST_MESSAGE_URL
    assert kwargs["json"] == {"channel": FNO_DESK_CHANNEL_ID, "text": "refused"}
    assert kwargs["headers"]["Authorization"] == f"Bearer {TOKEN}"


def test_slack_error_and_network_failure_are_reported_without_the_token():
    refused = SlackChannelAlerts(TOKEN, FNO_DESK_CHANNEL_ID, FakeSession({"ok": False, "error": "not_in_channel"}))
    assert refused.send("x") == "alert NOT sent: not_in_channel"
    offline = SlackChannelAlerts(TOKEN, FNO_DESK_CHANNEL_ID, FakeSession(error=requests.ConnectionError(TOKEN)))
    assert offline.send("x") == "alert NOT sent: ConnectionError"


def test_without_a_token_nothing_is_sent_and_the_outcome_says_so(monkeypatch):
    monkeypatch.delenv(ENV_FNO_SLACK_BOT_TOKEN, raising=False)
    assert isinstance(composition.build_alert_sender(), NoAlertSender)
    assert composition.build_alert_sender().send("x") == "alert NOT sent: FNO_SLACK_BOT_TOKEN is not set"
    monkeypatch.setenv(ENV_FNO_SLACK_BOT_TOKEN, TOKEN)
    assert isinstance(composition.build_alert_sender(), SlackChannelAlerts)
