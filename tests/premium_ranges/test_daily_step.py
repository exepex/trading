"""O1's `premium_ranges` step: right after G13's record, G13d's own receipts only, not live until a judged date."""

from datetime import date

from fno.constants import DAILY_RUN_STEPS, STEP_NOT_LIVE
from fno.daily.steps import Alerted, CommandStep, LiveFrom
from fno.premium_ranges.folders import receipt_pathspecs
from tests.daily.live_dates import without_live_dates
from tests.price_ranges.test_score_steps import day_steps

DAY = date(2026, 10, 22)


def test_the_issue_step_follows_g13s_record_with_its_own_receipts_and_is_not_live(monkeypatch):
    step = day_steps(monkeypatch, without_live_dates())["premium_ranges"]
    assert isinstance(step, Alerted) and isinstance(step.step, LiveFrom) and isinstance(step.step.step, CommandStep)
    command = step.step.step
    assert tuple(command.arguments(DAY)) == ("premrange", "issue", "--day", "2026-10-22", "--live")
    assert tuple(command.pathspecs) == receipt_pathspecs() == ("receipts/data/premium_ranges/v1/",)
    assert DAILY_RUN_STEPS.index("premium_ranges") == DAILY_RUN_STEPS.index("price_distribution") + 1
    assert step.step.live_from is None and step.run(DAY).result["status"] == STEP_NOT_LIVE
