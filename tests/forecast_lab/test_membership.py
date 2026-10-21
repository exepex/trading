"""Story FL1-1, criterion 7: the bot's membership in the lab's two channels, read-only (`conversations.info`, a GET),
never a test post; the token never appears in a line; `lab channels` exits 1 unless the bot is in both."""

from argparse import Namespace

import requests

from fno.constants import FNO_FORECAST_CHANNEL_ID, FNO_INTRADAY_CHANNEL_ID
from fno.forecast_lab.cli import cmd_lab
from fno.forecast_lab.membership import CONVERSATIONS_INFO_URL, check_membership

TOKEN = "test-token"


class Answer:
    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


class Session:
    """Records each call; `post` exists only to prove it is never called."""

    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def get(self, url, headers, params, timeout):
        self.calls.append((url, params["channel"]))
        answer = self.answers[params["channel"]]
        if isinstance(answer, Exception):
            raise answer
        return Answer(answer)

    def post(self, *args, **kwargs):
        raise AssertionError("a membership check never posts")


def test_both_channels_are_read_once_each_and_a_member_of_both_passes():
    member = {"ok": True, "channel": {"is_member": True}}
    session = Session({FNO_FORECAST_CHANNEL_ID: member, FNO_INTRADAY_CHANNEL_ID: member})
    lines, every = check_membership(session, TOKEN)
    assert every and lines == ["#fno-forecast: the bot is a member", "#fno-intraday: the bot is a member"]
    assert session.calls == [(CONVERSATIONS_INFO_URL, FNO_FORECAST_CHANNEL_ID),
                             (CONVERSATIONS_INFO_URL, FNO_INTRADAY_CHANNEL_ID)]  # fmt: skip


def test_not_a_member_or_no_answer_fails_and_says_why_without_the_token():
    session = Session({FNO_FORECAST_CHANNEL_ID: {"ok": True, "channel": {"is_member": False}},
                       FNO_INTRADAY_CHANNEL_ID: requests.ConnectionError(TOKEN)})  # fmt: skip
    lines, every = check_membership(session, TOKEN)
    assert not every and lines == ["#fno-forecast: the bot is NOT a member",
                                   "#fno-intraday: membership unknown (ConnectionError)"]  # fmt: skip
    refused = Session({FNO_FORECAST_CHANNEL_ID: {"ok": False, "error": "channel_not_found"},
                       FNO_INTRADAY_CHANNEL_ID: {"ok": True, "channel": {"is_member": True}}})  # fmt: skip
    lines, every = check_membership(refused, TOKEN)
    assert lines[0] == "#fno-forecast: membership unknown (channel_not_found)" and not every  # unknown never passes


def test_the_command_without_a_token_checks_nothing_and_exits_1():
    printed = []
    assert cmd_lab(Namespace(action="channels", day=None), out=printed.append, env={}) == 1
    assert printed == ["lab channels: FNO_SLACK_BOT_TOKEN is not set; membership not checked"]
