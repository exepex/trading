"""Story T1: `python -m fno card daily` (criteria 12 and 14): a dry run by default, on the real repository, with no
network call; `--post` issues the card and fails the exit code when it was not sent or not saved."""

from argparse import Namespace
from datetime import date

import pytest
import requests

from fno import cli
from fno.cards import cli as card_cli
from fno.cards import wiring
from fno.cards.issue import IssueResult


@pytest.fixture
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("a dry run made a network call")

    monkeypatch.setattr(requests.Session, "request", refuse)
    monkeypatch.setattr(requests, "head", refuse)


def run(on, post=False):
    out = []
    code = card_cli.cmd_card_daily(Namespace(on=on, post=post), out=out.append)
    return code, "\n".join(out)


def test_the_dry_run_prints_the_real_repositorys_card_and_issues_nothing(no_network, monkeypatch):
    monkeypatch.setattr(wiring, "build_card_issuer", lambda: pytest.fail("a dry run issued the card"))
    code, text = run(date(2026, 10, 15))
    assert code == 0 and text.startswith("PAPER ONLY.")
    assert "Status: NO TRADE" in text and text.endswith(card_cli.DRY_RUN)


def test_a_holiday_prints_not_a_trading_day(no_network):
    assert run(date(2026, 10, 2)) == (0, "not a trading day: no card for 2026-10-02")


class Issuer:
    def __init__(self, sent, saved):
        self.sent, self.saved, self.calls = sent, saved, []

    def issue(self, card, text):
        self.calls.append(text)
        return IssueResult(
            ("alert NOT sent: x",) if not self.sent else ("alert sent to #fno-desk",), self.sent, self.saved
        )


@pytest.mark.parametrize(("sent", "saved", "code"), [(True, True, 0), (False, True, 1), (True, False, 1)])
def test_post_issues_the_printed_card_and_the_exit_code_says_if_it_failed(monkeypatch, sent, saved, code):
    issuer = Issuer(sent, saved)
    monkeypatch.setattr(wiring, "build_card_issuer", lambda: issuer)
    result, text = run(date(2026, 10, 15), post=True)
    assert result == code and issuer.calls and text.startswith(issuer.calls[0])


def test_the_command_is_registered(monkeypatch):
    seen = []
    monkeypatch.setattr(card_cli, "cmd_card_witness", lambda args: seen.append(args.on) or 0)
    with pytest.raises(SystemExit):
        cli.main(["card", "daily", "--on", "not-a-date"])
    assert cli.main(["card", "witness", "--on", "2026-10-15"]) == 0 and seen == [date(2026, 10, 15)]
