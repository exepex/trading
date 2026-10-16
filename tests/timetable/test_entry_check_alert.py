"""Story E4c criterion 7: one #fno-desk line per entry the check refuses, ending "information, no action", with no
quote figure; without the token "alert NOT sent: <reason>" is printed and the run goes on to its exits."""

from dataclasses import replace

import pytest

from fno.alerts.sender import NoAlertSender
from fno.constants import BOOK1_RULES, OPTION_CALL, OUTCOME_NOT_OPENED
from fno.daily.alerts import ReportedAlerts
from tests.desk.builders import FLY_QUOTES, contract

from . import fakes
from .fakes import C4, Decisions, Rules, daily_run
from .test_daily_run import NORMAL, decided, run_day

WING = (25200, OPTION_CALL)


@pytest.fixture
def thin_wing(monkeypatch):
    """The day's execution snapshot: the call wing's bid size 64, below the 65 units it would have to sell back."""
    rows = fakes.fly_rows
    monkeypatch.setattr(fakes, "fly_rows", lambda: rows({WING: {"bid_qty": 64}}))


def refused_day(root, tmp_path, alerts):
    decisions = Decisions()
    decisions.add(*decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    run, clock, *_ = daily_run(root, tmp_path, alerts, (BOOK1_RULES,), decisions, C4(), Rules())
    return run, clock


def test_one_information_alert_with_no_quote_figure(root, tmp_path, alerts, thin_wing):
    run, clock = refused_day(root, tmp_path, alerts)
    log = run_day(run, clock, NORMAL)
    assert log.result("fills")["t1"]["outcome"] == OUTCOME_NOT_OPENED
    (alert,) = [a for a in alerts.sent if "not opened" in a]
    assert alert == (f"F&O paper desk {NORMAL} {BOOK1_RULES}: trade t1 not opened: protection_not_sellable "
                     f"({contract(*WING)}, 65 units): information, no action")  # fmt: skip
    figures = {f"{v:g}" for quote in FLY_QUOTES.values() for v in quote} | {"64"}
    rest = alert.replace(contract(*WING), "").replace("65 units", "").replace(str(NORMAL), "")
    assert not [f for f in figures if f in rest]


def test_without_the_token_it_prints_alert_not_sent_and_the_run_reaches_its_exits(root, tmp_path, thin_wing, capsys):
    """Through the daily run's one sender (story O1's `ReportedAlerts`, as `fno/daily/wiring.py` wires it), the unsent
    refusal is printed exactly once, never twice."""
    run, clock = refused_day(root, tmp_path, ReportedAlerts(NoAlertSender()))
    log = run_day(run, clock, NORMAL)
    out = capsys.readouterr().out.splitlines()
    unsent = [line for line in out if "alert NOT sent: FNO_SLACK_BOT_TOKEN is not set" in line and "trade" in line]
    assert len(unsent) == 1 and "not opened" in unsent[0]
    assert list(log.steps)[-2:] == ["exits", "trade_marks"]


def test_a_replayed_fills_step_sends_no_second_alert(root, tmp_path, alerts, thin_wing):
    """A fills step repeated after a stop (`enter` returns the recorded outcome) is never a new refusal."""
    run, clock = refused_day(root, tmp_path, alerts)
    log = run_day(run, clock, NORMAL)
    run.steps.fill(NORMAL, True, log.result("decisions"))
    assert len([a for a in alerts.sent if "not opened" in a]) == 1


def test_an_entry_refused_by_the_entry_limit_sends_no_e4c_alert(root, tmp_path, alerts):
    """Only the entry check's refusals alert: E4's entry limit records its reason and stays silent, as before."""
    decisions = Decisions()
    decision, (order,) = decided(BOOK1_RULES, "t1", NORMAL)
    decisions.add(decision, (replace(order, risk=replace(order.risk, entry_cash_rs=10_000_000.0)),), NORMAL)
    run, clock, *_ = daily_run(root, tmp_path, alerts, (BOOK1_RULES,), decisions, C4(), Rules())
    log = run_day(run, clock, NORMAL)
    assert log.result("fills")["t1"]["reason"].startswith("entry_worse_than_approved")
    assert not [a for a in alerts.sent if "not opened" in a]
