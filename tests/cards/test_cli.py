"""Story T1: `python -m fno card daily` (criteria 12 and 14): a dry run by default, on the real repository, with no
network call; `--post` issues the card and fails the exit code when it was not sent or not saved."""

from argparse import Namespace
from datetime import date, datetime

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


@pytest.fixture(autouse=True)
def today_is_the_15th(monkeypatch):
    from fno import models

    monkeypatch.setattr(models, "now_ist", lambda: datetime(2026, 10, 15, 15, 8, tzinfo=models.IST))


def run(on, post=False, test=False):
    out = []
    code = card_cli.cmd_card_daily(Namespace(on=on, post=post, test=test), out=out.append)
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

    def issue(self, card, text, test=False):
        self.calls.append((text, test))
        return IssueResult(
            ("alert NOT sent: x",) if not self.sent else ("alert sent to #fno-desk",), self.sent, self.saved
        )


@pytest.mark.parametrize(("sent", "saved", "code"), [(True, True, 0), (False, True, 1), (True, False, 1)])
def test_post_issues_the_printed_card_and_the_exit_code_says_if_it_failed(monkeypatch, sent, saved, code):
    issuer = Issuer(sent, saved)
    monkeypatch.setattr(wiring, "build_card_issuer", lambda: issuer)
    result, text = run(date(2026, 10, 15), post=True)
    assert result == code and issuer.calls[0][1] is False and text.startswith(issuer.calls[0][0])


def test_test_marks_one_live_post_and_needs_post(no_network, monkeypatch):
    monkeypatch.setattr(wiring, "build_card_issuer", lambda: pytest.fail("--test alone must not post"))
    assert run(date(2026, 10, 15), test=True) == (2, card_cli.TEST_NEEDS_POST)
    issuer = Issuer(True, True)
    monkeypatch.setattr(wiring, "build_card_issuer", lambda: issuer)
    assert run(date(2026, 10, 15), post=True, test=True)[0] == 0 and issuer.calls[0][1] is True


def test_the_command_is_registered(monkeypatch):
    seen = []
    monkeypatch.setattr(card_cli, "cmd_card_witness", lambda args: seen.append(args.on) or 0)
    with pytest.raises(SystemExit):
        cli.main(["card", "daily", "--on", "not-a-date"])
    assert cli.main(["card", "witness", "--on", "2026-10-15"]) == 0 and seen == [date(2026, 10, 15)]


def test_post_refuses_any_day_but_today(monkeypatch):
    """Judge 101 minor 1: today's records must never be issued as another day's card."""
    monkeypatch.setattr(wiring, "build_card_issuer", lambda: pytest.fail("another day's card was issued"))
    code, text = run(date(2026, 10, 14), post=True)
    assert code == 2 and text == card_cli.POST_TODAY_ONLY.format(day=date(2026, 10, 14), today=date(2026, 10, 15))
    assert run(date(2026, 10, 14))[0] == 0  # a dry run of another day stays allowed
