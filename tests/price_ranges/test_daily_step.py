"""G13b criterion 10: O1's `price_ranges` step, wired as G13's: Alerted(LiveFrom(CommandStep)) right after G13's
`price_distribution`, G13b's receipts its only pathspecs, not live without a date."""

from datetime import date

from fno.config import load_app_config
from fno.constants import DAILY_RUN_STEPS, STEP_NOT_LIVE
from fno.daily.steps import Alerted, CommandStep, LiveFrom
from fno.price_ranges.folders import receipt_pathspecs

DAY = date(2026, 10, 16)


def built_step(monkeypatch):
    from fno.daily import wiring

    seen = {}
    monkeypatch.setattr("fno.desk.daily_wiring.build_daily_run", lambda *a, **k: seen.update(k) or object())
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_orders", lambda *args: None)
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_exit_rules", lambda *args: None)
    wiring.build_day_runner(load_app_config())
    return seen["day_steps"]["price_ranges"]


def test_the_step_is_wired_after_g13_with_g13bs_receipts_only_and_not_live(monkeypatch):
    step = built_step(monkeypatch)
    assert isinstance(step, Alerted) and isinstance(step.step, LiveFrom) and isinstance(step.step.step, CommandStep)
    command = step.step.step
    assert tuple(command.arguments(DAY)) == ("pricerange", "issue", "--at", "1545", "--day", "2026-10-16", "--live")
    assert tuple(command.pathspecs) == receipt_pathspecs() == ("receipts/data/price_ranges/v1/",)
    assert DAILY_RUN_STEPS.index("price_ranges") == DAILY_RUN_STEPS.index("price_distribution") + 1
    assert step.step.live_from is None and step.run(DAY).result["status"] == STEP_NOT_LIVE
