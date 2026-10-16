"""Story E2d end to end in E3's daily run: the `marks` step after the exits values each open trade at the session's
own recorded execution snapshot, as scoreboard B values it, so a trade opened today is valued today."""

import csv

from fno.books.account import PaperAccount
from fno.books.trade_marks import TRADE_MARKS_FILE, VALUED
from fno.constants import BOOK1_RULES, BOOK2_HYBRID
from fno.desk.records import DeskRecords
from fno.desk.snapshot import RecordedExecutionSnapshots
from fno.scoreboard.committed_runs import CommittedRuns
from fno.scoreboard.daily_values import trade_days
from fno.scoreboard.sources import SnapshotMarks
from tests.checks.builders import CALENDAR

from .test_daily_run import NORMAL, SLOW, run_day, week  # noqa: F401 - the five-day fixture


def trade_rows(root, book):
    return list(csv.DictReader(PaperAccount(root, book).file(TRADE_MARKS_FILE).open(encoding="utf-8")))


def s2_value(root, store, book, trade_id, day):
    account = PaperAccount(root, book)
    fills = [f for f in account.fills() if f.trade_id == trade_id]
    marks = SnapshotMarks(RecordedExecutionSnapshots(store), CommittedRuns(root).snapshot_ids())
    days = CALENDAR.sessions(fills[0].filled_at.date(), day)
    return trade_days(fills, DeskRecords(account).legs(trade_id), days, marks)[-1].value


def test_the_run_marks_today_s_open_trades_as_scoreboard_b_values_them(root, week):  # noqa: F811
    run, clock, capture, *_ = week
    for day in (NORMAL, SLOW):
        log = run_day(run, clock, day)
        assert log.result("trade_marks")[BOOK1_RULES]["equity_row"] is True
    rows = trade_rows(root, BOOK1_RULES)
    expected = [(str(NORMAL), "t1", VALUED), (str(SLOW), "t1", VALUED), (str(SLOW), "t2", VALUED)]
    assert [(r["date"], r["trade_id"], r["status"]) for r in rows] == expected
    for row, day in zip(rows, (NORMAL, SLOW, SLOW), strict=True):
        assert float(row["value_rs"]) == round(s2_value(root, capture.store, BOOK1_RULES, row["trade_id"], day), 2)
    history = {r["date"]: r for r in PaperAccount(root, BOOK1_RULES).equity_history()}
    marked = sum(float(r["value_rs"]) for r in rows if r["date"] == str(SLOW))
    slow = history[str(SLOW)]
    assert float(slow["marked_equity_rs"]) == round(float(slow["closed_equity_rs"]) + marked, 2)
    assert log.result("trade_marks")[BOOK2_HYBRID]["marked"] is True
