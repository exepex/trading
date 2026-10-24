"""Story E8 rule 11: when today's owner-timing fills failed or were refused, no book opens anything new today, since C2
would see open risk without this morning's fills; exits still run. A step that ran, or one not run (before E8 is live),
blocks nothing."""

from datetime import date

import pytest

from fno.books.account import PaperAccount
from fno.constants import (
    BOOK1_RULES,
    OUTCOME_OPENED,
    OWNER_TIMING_STEP,
    STEP_FAILED,
    STEP_NOT_LIVE,
    STEP_OK,
    STEP_REFUSED,
)
from fno.desk.daily_ports import DayStep
from fno.desk.daily_steps import StepOutcome
from fno.desk.exit_rules import TimeExit
from fno.desk.records import DeskRecords
from tests.desk.builders import at

from .fakes import C4, Decisions, Rules, daily_run
from .test_daily_run import decided

DAY = date(2026, 10, 14)


def fills(root):
    return DeskRecords(PaperAccount(root, BOOK1_RULES)).fill_rows()


class Fills(DayStep):
    def __init__(self, status: str):
        self.status = status

    def run(self, day):
        return StepOutcome({}, {"status": self.status, "reason": "fixture"})


def run_with(root, tmp_path, alerts, status: str | None):
    decisions = Decisions()
    decisions.add(*decided(BOOK1_RULES, "t1", DAY), DAY)
    run, clock, _, _ = daily_run(root, tmp_path, alerts, (BOOK1_RULES,), decisions, C4(), Rules({"t1": [TimeExit(11)]}))
    if status is not None:
        run.day_steps[OWNER_TIMING_STEP] = Fills(status)
    clock.now = at(14, 50, day=DAY)
    return run.run(DAY)


@pytest.mark.parametrize("status", [STEP_FAILED, STEP_REFUSED])
def test_failed_or_refused_fills_block_every_books_new_entries(root, tmp_path, alerts, status):
    log = run_with(root, tmp_path, alerts, status)
    assert "t1" not in log.result("fills")
    assert f"today's owner-timing fills {status} (fixture)" in log.result("fills")[BOOK1_RULES]["reason"]
    assert log.done("exits") and not fills(root)


@pytest.mark.parametrize("status", [STEP_OK, STEP_NOT_LIVE, None], ids=["ran", "not live", "not run"])
def test_fills_that_ran_or_did_not_run_block_nothing(root, tmp_path, alerts, status):
    assert run_with(root, tmp_path, alerts, status).result("fills")["t1"]["outcome"] == OUTCOME_OPENED
