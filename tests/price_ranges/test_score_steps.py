"""G13's and G13b's daily score steps (orchestrator, 21 Oct: phase-1 completion): each wired as
Alerted(LiveFrom(CommandStep)) right after its own issue step, its story's receipts as its only pathspecs (G13b's
seals and scores, G13's scores), not live without its own `daily.live_from` date."""

from datetime import date

import pytest

from fno.config import load_app_config
from fno.constants import DAILY_RUN_STEPS, STEP_NOT_LIVE
from fno.daily.steps import Alerted, CommandStep, LiveFrom
from fno.price_distribution.folders import receipt_pathspecs as distribution_receipts
from fno.price_ranges.folders import receipt_pathspecs as range_receipts
from tests.daily.live_dates import without_live_dates

DAY = date(2026, 10, 16)


def day_steps(monkeypatch, cfg=None) -> dict:
    from fno.daily import wiring

    seen = {}
    monkeypatch.setattr("fno.desk.daily_wiring.build_daily_run", lambda *a, **k: seen.update(k) or object())
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_orders", lambda *args: None)
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_exit_rules", lambda *args: None)
    wiring.build_day_runner(cfg or load_app_config())
    return seen["day_steps"]


@pytest.mark.parametrize(
    ("name", "after", "arguments", "pathspecs"),
    [
        ("price_distribution_scores", "price_distribution", ("pricedist", "score"), distribution_receipts()),
        ("price_range_scores", "price_ranges", ("pricerange", "score"), range_receipts()),
    ],
)
def test_each_score_step_follows_its_issue_with_its_own_receipts_and_is_not_live(monkeypatch, name, after, arguments,
                                                                                  pathspecs):  # fmt: skip
    step = day_steps(monkeypatch, without_live_dates())[name]
    assert isinstance(step, Alerted) and isinstance(step.step, LiveFrom) and isinstance(step.step.step, CommandStep)
    command = step.step.step
    assert tuple(command.arguments(DAY)) == arguments and tuple(command.pathspecs) == pathspecs
    assert DAILY_RUN_STEPS.index(name) == DAILY_RUN_STEPS.index(after) + 1
    assert step.step.live_from is None and step.run(DAY).result["status"] == STEP_NOT_LIVE


def test_the_range_scores_run_before_the_last_steps_of_the_day():
    assert DAILY_RUN_STEPS.index("price_range_scores") < DAILY_RUN_STEPS.index("candles")


def test_each_score_step_reads_its_own_live_date_never_its_issue_step_s(monkeypatch):
    """Judge 423 minor 1: with every key null, a step reading another step's key would pass; distinct dates catch it."""
    dates = {"price_distribution": "2026-11-02", "price_distribution_scores": "2026-11-03",
             "price_ranges": "2026-11-04", "price_range_scores": "2026-11-05"}  # fmt: skip
    cfg = without_live_dates()
    cfg = {**cfg, "daily": {**cfg["daily"], "live_from": {**cfg["daily"]["live_from"], **dates}}}
    steps = day_steps(monkeypatch, cfg)
    assert {name: steps[name].step.live_from.isoformat() for name in dates} == dates
