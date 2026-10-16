"""LM1 criterion 6: every alert starts "F&O monitor:", its first line is an action or "information, no action", it
states the 60-minute assumption, and no alert says exit or close or names a contract's price (index levels allowed)."""

from __future__ import annotations

import re

import pytest

from fno.monitor.checks import BigMove, ExitRuleReached, LossUsed, QuotesStale, ShortStrikeNear
from fno.monitor.limits import AlertLimits, SentAlert
from fno.monitor.model import DANGER
from fno.monitor.texts import INFORMATION, PREFIX, alert_text

from .fixtures import at, mark, settings, spread

S = settings()
FORBIDDEN = re.compile(r"exit|close", re.IGNORECASE)


def every_alert(hhmm="10:30") -> list[str]:
    m = mark(hhmm, level=24600.0, previous=25000.0)
    positions = [spread(loss=8500.0, short=24500.0, exit_rules_reached=("profit_target", "stop_loss", "time_exit")),
                 spread("T2", loss=None)]  # fmt: skip
    found = [c for check in (LossUsed(S), ShortStrikeNear(S), ExitRuleReached(S), BigMove(S))
             for c in check.find(m, positions)]  # fmt: skip
    found += QuotesStale(S).find(mark(hhmm, status="missed", last_good=at("09:15")), at("09:15"))
    history = [SentAlert(f"x{n}", DANGER, at("09:30")) for n in range(10)]
    summary = AlertLimits(S).decide([found[0]], history, m).summary
    return [alert_text(c, m, S) for c in [*found, summary]]


def test_every_kind_of_alert_is_covered():
    checks = {"loss_used", "cannot_mark", "short_strike_near", "exit_rule_reached", "big_move", "quotes_stale"}
    assert len(every_alert()) >= len(checks) + 1


@pytest.mark.parametrize("text", every_alert())
def test_each_alert_follows_the_first_line_rule(text):
    first = text.splitlines()[0]
    assert first.startswith(PREFIX + " ")
    assert first.endswith(INFORMATION) or ", action: " in first
    assert "60 minutes later" in text.splitlines()[-1]
    assert not FORBIDDEN.search(text), text
    assert "Rs " not in text or "loss used" in text  # rupees only for the position's own loss, never a price


def test_an_exit_rule_reached_is_information_with_no_e8_words():
    texts = [t for t in every_alert() if "rule at" in t]
    assert len(texts) == 3
    assert all(t.splitlines()[0] == f"{PREFIX} DANGER, {INFORMATION}" for t in texts)
    assert not any("paper desk" in t for t in texts)


@pytest.mark.parametrize(("hhmm", "when"), [("15:00", "today's execution snapshot (15:15)"),
                                            ("15:15", "the next session's execution snapshot (15:15)")])  # fmt: skip
def test_the_60_minute_line_names_the_next_execution_snapshot(hhmm, when):
    assert all(when in t.splitlines()[-1] for t in every_alert(hhmm))


def test_index_levels_are_allowed():
    assert any("NIFTY 24,600.00" in t for t in every_alert())
