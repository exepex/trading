"""FL1-1: O1's `lab_close` step, agreed with the O1 builder: Alerted(LiveFrom(NotBefore(CommandStep))) as the run's
last step, after `candles`, waiting for 15:45, committing only the lab's own receipts, and not live (so never waiting)
until `daily.live_from.lab_close` is set."""

from datetime import date, time

from fno.config import load_app_config
from fno.constants import DAILY_RUN_STEPS, STEP_NOT_LIVE
from fno.daily.steps import Alerted, CommandStep, LiveFrom, NotBefore
from fno.forecast_lab.wiring import receipt_pathspecs
from tests.daily.live_dates import without_live_dates

DAY = date(2026, 10, 21)


def built_step(monkeypatch, cfg=None):
    from fno.daily import wiring

    seen = {}
    monkeypatch.setattr("fno.desk.daily_wiring.build_daily_run", lambda *a, **k: seen.update(k) or object())
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_orders", lambda *args: None)
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_exit_rules", lambda *args: None)
    wiring.build_day_runner(cfg or load_app_config())
    return seen["day_steps"]["lab_close"]


def test_the_step_is_last_after_the_candles_and_waits_for_15_45(monkeypatch):
    step = built_step(monkeypatch)
    assert isinstance(step, Alerted) and step.name == "lab_close" and isinstance(step.step, LiveFrom)
    waiting = step.step.step
    assert isinstance(waiting, NotBefore) and waiting.at == time(15, 45) and isinstance(waiting.step, CommandStep)
    assert tuple(waiting.step.arguments(DAY)) == ("lab", "close", "--day", "2026-10-21")
    assert DAILY_RUN_STEPS[-2:] == ("candles", "lab_close")


def test_it_commits_only_the_lab_s_own_receipts():
    assert receipt_pathspecs() == ("receipts/data/forecast_lab/v1/close/",)


def test_not_live_returns_at_once_without_waiting_for_15_45(monkeypatch):
    step = built_step(monkeypatch, without_live_dates())
    waited = []
    step.step.step.waiter = type("Waiter", (), {"until": lambda self, at: waited.append(at)})()
    assert step.step.live_from is None and step.run(DAY).result["status"] == STEP_NOT_LIVE and waited == []
