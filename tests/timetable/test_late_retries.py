"""Judge 569.3 M1 (O1 R2 follow-up): the routine's immediate rerun (CLAUDE.md step 2b) comes after the first run ends,
so after 15:20. A retried exits or trade_marks step then runs and does its work, never refused by the fills' own
`fills_by` limit (`DailyRun._too_late`), and writes nothing twice. The same holds for decision 47's rerun after a stop
at the fills: its fills are refused late, its exits and marks run (the self-review's finding 2)."""

from datetime import timedelta

import pytest

from fno.books.account import PaperAccount
from fno.books.trade_marks import TRADE_MARKS_FILE
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, OUTCOME_CLOSED, STEP_FAILED, STEP_REFUSED
from fno.desk.daily_run import RunStopped
from fno.desk.exit_rules import TimeExit
from fno.desk.records import DeskRecords
from fno.desk.run_log import RETRY
from tests.desk.builders import at

from .fakes import C4, Decisions, LocalSync, Rules, daily_run
from .test_daily_run import NORMAL, decided, events, fills, run_day
from .test_failed_step_retry import DUE, Flaky, ledger, trade_open_on_normal
from .test_fills_final import WrittenThenCommitFailing

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
    before = written_rows(root)

    clock.now = at(15, 20, day=DUE) + after
    log = run.run(DUE)
    assert flaky.calls == 2 and log.result("exits").get("status") not in (STEP_FAILED, STEP_REFUSED)
    assert log.result("exits")[BOOK1_RULES]["reviewed"] is True
    assert_closed_once_at_the_snapshot(root, log.result("snapshot")["snapshot_id"])
    if written:  # the closes written before the error: the retry adds no row anywhere
        assert written_rows(root) == before


def written_rows(root):
    return fills(root, BOOK1_RULES), ledger(root, BOOK1_RULES), event_rows(root)


def event_rows(root):
    return DeskRecords(PaperAccount(root, BOOK1_RULES)).event_rows()


def assert_closed_once_at_the_snapshot(root, snapshot_id):
    """t1 closed once: one `closed` event row, one close per leg at the day's own snapshot, one ledger row per fill."""
    rows = fills(root, BOOK1_RULES)
    closes = [r for r in rows if r["action"] == "close"]
    assert [(e["trade_id"], e["outcome"]) for e in event_rows(root)].count(("t1", OUTCOME_CLOSED)) == 1
    assert len(closes) == len({r["contract"] for r in rows}) and len({r["fill_id"] for r in rows}) == len(rows)
    assert {r["snapshot_id"] for r in closes} == {snapshot_id}  # never a price taken after 15:20
    entries = [r["entry_id"] for r in ledger(root, BOOK1_RULES)]
    assert len(entries) == len(set(entries)) and set(entries) >= {r["fill_id"] for r in rows}


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
    marks = PaperAccount(root, BOOK1_RULES).file(TRADE_MARKS_FILE).read_text(encoding="utf-8")
    assert f"{NORMAL.isoformat()},t1," in marks
    retried = account_files(root)
    flaky.real(NORMAL)  # marking once more changes no byte: the retry wrote the day's rows once, in place
    assert account_files(root) == retried


@pytest.mark.parametrize("after", LATE)
def test_a_rerun_after_a_stop_past_fills_by_refuses_the_fills_but_runs_the_exits_and_the_marks(root, tmp_path, alerts,
                                                                                               after):  # fmt: skip
    """Decision 47's rerun on a day t1's exit is due: book 2's commit fails inside the fills, so neither the exits nor
    the marks ran. The rerun past 15:20 refuses the fills (`FILLS_LATE`), then reviews the exits and marks the day."""
    decisions = Decisions()
    decisions.add(*decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    decisions.add(*decided(BOOK2_HYBRID, "d1", DUE), DUE)
    run, clock, *_ = daily_run(root, tmp_path, alerts, (BOOK1_RULES, BOOK2_HYBRID), decisions, C4(),
                               Rules({"t1": [TimeExit(11)]}))  # fmt: skip
    for session in (NORMAL, NORMAL + timedelta(days=1)):  # the session before DUE runs too, so no book is blocked
        run_day(run, clock, session)
    run.steps.sync = WrittenThenCommitFailing(root, BOOK2_HYBRID)
    with pytest.raises(RunStopped, match="run STOPPED at step fills"):
        run_day(run, clock, DUE)
    run.steps.sync = LocalSync(root)
    assert ("t1", OUTCOME_CLOSED) not in events(root, BOOK1_RULES) and fills(root, BOOK2_HYBRID)  # d1 written
    opened = fills(root, BOOK2_HYBRID)

    clock.now = at(15, 20, day=DUE) + after
    log = run.run(DUE)
    assert log.result("fills")["status"] == STEP_REFUSED and fills(root, BOOK2_HYBRID) == opened
    assert log.result("exits")[BOOK1_RULES]["reviewed"] is True
    assert log.result("trade_marks").get("status") not in (STEP_FAILED, STEP_REFUSED)
    assert_closed_once_at_the_snapshot(root, log.result("snapshot")["snapshot_id"])
