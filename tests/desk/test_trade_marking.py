"""Story E2d criteria 1, 2, 4, 5, 7, 8 and 11: each open trade marked once a session by S2's rule (imported unchanged),
its row in `trade_marks.csv` and the account's equity row, with no value read back from what the marking wrote."""

import csv
from datetime import date, datetime, time

import pytest

from fno.books.account import PaperAccount
from fno.books.daily_totals import write_daily_totals
from fno.books.trade_marks import AWAITING_SETTLEMENT, TRADE_MARKS_FILE, UNMARKED, VALUED
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, FILL_CLOSE, FILL_OPEN, SIDE_BUY, SIDE_SELL
from fno.desk.pricing import DeskLeg
from fno.desk.records import DeskRecords
from fno.desk.trade_marking import TradeMarker
from fno.desk.wiring import open_desk_journal
from fno.models import IST
from fno.research_engine.structures import BOUGHT, SOLD, Leg
from fno.scoreboard.daily_values import trade_days
from fno.scoreboard.sources import SnapshotMarks
from tests.scorecard.history import LONG, SHORT, UNITS, TouchSnapshots, _record, trade

D1, D2, D3, D4 = date(2026, 10, 14), date(2026, 10, 15), date(2026, 10, 16), date(2026, 10, 19)
DAYS = (D1, D2, D3, D4)


def sessions(first, last):
    return [d for d in DAYS if first <= d <= last]


def quotes(*days_mids, legs=(LONG, SHORT)):
    """Each day's valid snapshot `valid-<day>` with the given mids (None: no quote for that leg)."""
    snaps, ids = TouchSnapshots(), {}
    for day, mids in days_mids:
        ids[day] = f"valid-{day}"
        for leg, mid in zip(legs, mids, strict=True):
            if mid is not None:
                snaps.add(day, ids[day], leg, mid - 0.5, mid + 0.5)
    return snaps, ids


def mark(root, book, day, snaps, ids):
    with open_desk_journal(book, root) as journal:
        return TradeMarker(sessions, SnapshotMarks(snaps, ids)).mark(journal, day)


def s2(root, book, trade_id, day, snaps, ids):
    """Scoreboard B's value of the trade on `day`, straight from S2's code."""
    account = PaperAccount(root, book)
    fills = [f for f in account.fills() if f.trade_id == trade_id]
    legs = DeskRecords(account).legs(trade_id)
    return trade_days(fills, legs, sessions(fills[0].filled_at.date(), day), SnapshotMarks(snaps, ids))[-1]


def rows(root, book, name=TRADE_MARKS_FILE):
    path = PaperAccount(root, book).file(name)
    return list(csv.DictReader(path.open(encoding="utf-8"))) if path.exists() else []


def flow(root, book, trade_id):
    return sum(f.amount for f in PaperAccount(root, book).fills() if f.trade_id == trade_id)


def test_same_as_s2_every_session_a_stale_day_and_a_lost_marking_day(root):
    """Criterion 1: day 2's marking is lost after its valid snapshot was recorded, and day 3 has no short quote: day 3
    is valued at day 2's mid from the snapshot history, as S2 values it, never at day 1's from the marks file."""
    trade(root, BOOK1_RULES, "fly", "t1", D1)
    snaps, ids = quotes((D1, (19.0, 69.0)), (D2, (15.0, 55.0)), (D3, (12.0, None)))
    mark(root, BOOK1_RULES, D1, snaps, ids)  # day 2: no marking ran
    marked = mark(root, BOOK1_RULES, D3, snaps, ids)
    (day3,) = marked.marks
    assert day3.value == s2(root, BOOK1_RULES, "t1", D3, snaps, ids).value
    assert day3.value == pytest.approx(flow(root, BOOK1_RULES, "t1") + UNITS * 12.0 - UNITS * 55.0)  # day 2's short
    assert day3.value != pytest.approx(flow(root, BOOK1_RULES, "t1") + UNITS * 12.0 - UNITS * 69.0)  # not day 1's
    assert (day3.status, day3.contracts) == (VALUED, (SHORT.contract,))
    assert day3.mark_value == pytest.approx(day3.value - flow(root, BOOK1_RULES, "t1"))
    assert [(r["date"], r["trade_id"], r["status"], r["contracts"]) for r in rows(root, BOOK1_RULES)] == [
        ("2026-10-14", "t1", VALUED, ""), ("2026-10-16", "t1", VALUED, SHORT.contract)]  # fmt: skip


def test_the_equity_row_is_closed_equity_plus_the_open_trades_values(root):
    """Criterion 2, with two open trades: never closed equity plus the legs alone."""
    trade(root, BOOK1_RULES, "fly", "t1", D1)
    trade(root, BOOK1_RULES, "fly", "t2", D1, credit=40.0)
    snaps, ids = quotes((D1, (19.0, 69.0)), (D2, (15.0, None)))
    mark(root, BOOK1_RULES, D1, snaps, ids)
    marked = mark(root, BOOK1_RULES, D2, snaps, ids)
    (row,) = [r for r in PaperAccount(root, BOOK1_RULES).equity_history() if r["date"] == "2026-10-15"]
    closed = float(row["closed_equity_rs"])
    assert float(row["marked_equity_rs"]) == pytest.approx(closed + sum(m.value for m in marked.marks), abs=0.005)
    legs_only = sum(m.mark_value for m in marked.marks)
    assert float(row["marked_equity_rs"]) != pytest.approx(closed + legs_only, abs=1.0)
    assert (row["open_trades"], row["stale_marks"]) == ("2", SHORT.contract)


def test_only_the_recorded_valid_snapshot_is_read_never_a_later_capture(root):
    """Criterion 4: a later capture of day 2 with other mids sits in the store; the run log names the valid one."""
    trade(root, BOOK1_RULES, "fly", "t1", D1)
    snaps, ids = quotes((D1, (19.0, 69.0)), (D2, (15.0, 55.0)))
    snaps.add(D2, "later", LONG, 99.5, 100.5)
    snaps.add(D2, "later", SHORT, 0.5, 1.5)
    (day2,) = mark(root, BOOK1_RULES, D2, snaps, ids).marks
    assert day2.value == pytest.approx(flow(root, BOOK1_RULES, "t1") + UNITS * 15.0 - UNITS * 55.0)


def test_a_rerun_gives_the_same_bytes_and_a_same_day_top_up_row_is_replaced(root):
    """Criterion 5."""
    trade(root, BOOK1_RULES, "fly", "t1", D1)
    snaps, ids = quotes((D1, (19.0, 69.0)))
    mark(root, BOOK1_RULES, D1, snaps, ids)
    account = PaperAccount(root, BOOK1_RULES)
    first = (account.file(TRADE_MARKS_FILE).read_bytes(), account.file("equity_history.csv").read_bytes())
    mark(root, BOOK1_RULES, D1, snaps, ids)
    assert (account.file(TRADE_MARKS_FILE).read_bytes(), account.file("equity_history.csv").read_bytes()) == first
    with open_desk_journal(BOOK2_HYBRID, root) as journal:
        start = journal.writer.account.capital()
        journal.writer.top_up(datetime.combine(D2, time(9, 0), IST), start + 1000.0)
    mark(root, BOOK2_HYBRID, D2, snaps, ids)
    days = [r["date"] for r in PaperAccount(root, BOOK2_HYBRID).equity_history()]
    assert days.count("2026-10-15") == 1


def test_marking_leaves_the_public_daily_totals_unchanged(root):
    """Criterion 7."""
    trade(root, BOOK1_RULES, "fly", "t1", D1)
    before = write_daily_totals(root, BOOK1_RULES).read_bytes()
    mark(root, BOOK1_RULES, D1, *quotes((D1, (19.0, 69.0))))
    assert write_daily_totals(root, BOOK1_RULES).read_bytes() == before


def test_a_book_with_no_open_trade_gets_its_equity_row_and_no_trade_rows(root):
    """Criterion 8."""
    assert mark(root, BOOK2_HYBRID, D1, *quotes()).marks == ()
    assert not PaperAccount(root, BOOK2_HYBRID).file(TRADE_MARKS_FILE).exists()
    (row,) = [r for r in PaperAccount(root, BOOK2_HYBRID).equity_history() if r["date"] == "2026-10-14"]
    assert row["marked_equity_rs"] == row["closed_equity_rs"] and row["open_trades"] == "0"


def test_a_leg_never_quoted_leaves_the_trade_unmarked_and_the_equity_row_unwritten(root):
    """Criterion 3's account side (its alert: test_trade_marking_step.py)."""
    trade(root, BOOK1_RULES, "fly", "t1", D2)
    before = PaperAccount(root, BOOK1_RULES).equity_history()
    (t1,) = mark(root, BOOK1_RULES, D2, *quotes((D2, (15.0, None)))).marks
    assert (t1.status, t1.value, t1.mark_value, t1.contracts) == (UNMARKED, None, None, (SHORT.contract,))
    assert PaperAccount(root, BOOK1_RULES).equity_history() == before
    assert rows(root, BOOK1_RULES)[0]["value_rs"] == ""


SOON = date(2026, 10, 15)
LONG_SOON = DeskLeg("NIFTY15OCT25200CE", SOON, Leg(25200, "CE", BOUGHT))
SHORT_SOON = DeskLeg("NIFTY15OCT25000CE", SOON, Leg(25000, "CE", SOLD))


def test_a_stale_leg_past_its_expiry_awaits_settlement_with_s2_s_value_then_leaves_the_list(root):
    """Criterion 11: before NSE's settlement price, S2's stale value labelled `awaiting_settlement`; after E7's
    settlement fills the trade is closed and no longer listed."""
    with open_desk_journal(BOOK1_RULES, root) as journal:
        journal.record_fill(_record(root, BOOK1_RULES, "fly", "e1", FILL_OPEN, LONG_SOON, SIDE_BUY, 20.0, 0.5, D1))
        journal.record_fill(_record(root, BOOK1_RULES, "fly", "e1", FILL_OPEN, SHORT_SOON, SIDE_SELL, 70.0, 0.5, D1))
    snaps, ids = quotes((D1, (19.0, 69.0)), (D2, (5.0, 30.0)), legs=(LONG_SOON, SHORT_SOON))
    (e1,) = mark(root, BOOK1_RULES, D3, snaps, ids).marks
    assert (e1.status, e1.value) == (AWAITING_SETTLEMENT, s2(root, BOOK1_RULES, "e1", D3, snaps, ids).value)
    assert e1.contracts == (SHORT_SOON.contract, LONG_SOON.contract)  # sorted, as S2 lists them
    with open_desk_journal(BOOK1_RULES, root) as journal:  # E7's settlement at NSE's final prices
        journal.record_fill(_record(root, BOOK1_RULES, "fly", "e1", FILL_CLOSE, LONG_SOON, SIDE_SELL, 0.0, 0.0, D4))
        journal.record_fill(_record(root, BOOK1_RULES, "fly", "e1", FILL_CLOSE, SHORT_SOON, SIDE_BUY, 0.0, 0.0, D4))
    assert mark(root, BOOK1_RULES, D4, snaps, ids).marks == ()
    assert [r["date"] for r in rows(root, BOOK1_RULES)] == ["2026-10-16"]
