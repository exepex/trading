"""Judge 569.3 M1 (O1 R2 follow-up): the routine's immediate rerun (CLAUDE.md step 2b) comes after the first run ends,
so after 15:20. A retried exits or trade_marks step then runs and does its work, never refused by the fills' own
`fills_by` limit (`DailyRun._too_late`), and writes nothing twice."""

from datetime import timedelta

import pytest

from fno.books.account import PaperAccount
from fno.books.trade_marks import TRADE_MARKS_FILE
from fno.constants import BOOK1_RULES, OUTCOME_CLOSED, STEP_FAILED, STEP_REFUSED
from fno.desk.run_log import RETRY
from tests.desk.builders import at

from .test_daily_run import NORMAL, events, fills, run_day
from .test_failed_step_retry import DUE, Flaky, ledger, trade_open_on_normal

# boundary: one second past fills_by; the routine's usual rerun after the run's end; a late evening rerun
LATE = [timedelta(seconds=1), timedelta(minutes=50), timedelta(hours=8, minutes=30)]


def account_files(root):
    account = PaperAccount(root, BOOK1_RULES)
    return {name: account.file(name).read_bytes() for name in (TRADE_MARKS_FILE, "equity_history.csv")}


@pytest.mark.parametrize("after", LATE)
@pytest.mark.parametrize("written", [True, False])  # the error after every write, or before any (empty)
def test_an_exits_retry_after_fills_by_reviews_the_exits_and_closes_each_leg_once(root, tmp_path, alerts, after,
                                                                                   written):  # fmt: skip
    run, clock, *_ = trade_open_on_normal(root, tmp_path, alerts)
    run_day(run, clock, NORMAL)
    flaky = run.steps.review_exits = Flaky(run.steps.review_exits, after=written)
    log = run_day(run, clock, DUE)
    assert log.result("exits")[RETRY] is True and (("t1", OUTCOME_CLOSED) in events(root, BOOK1_RULES)) is written

    clock.now = at(15, 20, day=DUE) + after
    log = run.run(DUE)
    assert flaky.calls == 2 and log.result("exits").get("status") not in (STEP_FAILED, STEP_REFUSED)
    assert log.result("exits")[BOOK1_RULES]["reviewed"] is True and ("t1", OUTCOME_CLOSED) in events(root, BOOK1_RULES)
    closes = [r for r in fills(root, BOOK1_RULES) if r["action"] == "close"]
    assert len(closes) == len({r["contract"] for r in fills(root, BOOK1_RULES)})  # each leg closed once
    assert len({r["fill_id"] for r in fills(root, BOOK1_RULES)}) == len(fills(root, BOOK1_RULES))
    assert len(ledger(root, BOOK1_RULES)) == len({tuple(r.items()) for r in ledger(root, BOOK1_RULES)})


@pytest.mark.parametrize("after", LATE)
@pytest.mark.parametrize("written", [True, False])
def test_a_marks_retry_after_fills_by_marks_the_day_and_writes_each_row_once(root, tmp_path, alerts, after, written):
    run, clock, *_ = trade_open_on_normal(root, tmp_path, alerts)
    flaky = run.marking.run = Flaky(run.marking.run, after=written)
    log = run_day(run, clock, NORMAL)
    assert log.result("trade_marks")[RETRY] is True

    clock.now = at(15, 20, day=NORMAL) + after
    log = run.run(NORMAL)
    assert flaky.calls == 2 and log.result("trade_marks").get("status") not in (STEP_FAILED, STEP_REFUSED)
    assert log.result("trade_marks")[BOOK1_RULES]["marked"] is True
    account = PaperAccount(root, BOOK1_RULES)
    assert [r["date"] for r in account.equity_history()].count(NORMAL.isoformat()) == 1
    retried = account_files(root)
    flaky.real(NORMAL)  # marking once more changes no byte: the retry wrote the day's rows once, in place
    assert account_files(root) == retried
