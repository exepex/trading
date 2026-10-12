"""Story E1: the committed starting accounts, the account measures, idempotent fills and the book firewall."""

import json
import os
from datetime import date, datetime

import pytest

from fno.accounting.ledgers import Order, trade_line
from fno.books.account import STARTING_CASH_RS, AccountError, AccountWriter, PaperAccount
from fno.books.equity import Mark, MissingMark
from fno.books.fills import Fill, FillError
from fno.books.lock import AccountLock, Lease
from fno.books.paths import BookPathError, account_folder
from fno.composition import build_paper_account, open_account_writer
from fno.config import ROOT, load_config
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI, BOOKS
from fno.models import IST

CHARGES = load_config(ROOT / "config.yaml")["charges"]
DAY = date(2026, 10, 13)


def fill(fill_id, trade_id, contract, side, price, units=65, pad=0.5, hour=15):
    when = datetime(2026, 10, 13, hour, 5, tzinfo=IST)
    return Fill.priced(fill_id, trade_id, when, contract, Order(side, price, units, pad), CHARGES)


@pytest.fixture
def root(tmp_path):
    for book in BOOKS:
        with open_account_writer(book, tmp_path) as writer:
            assert writer.start(DAY)
    return tmp_path


def test_the_committed_starting_state_is_rs_5_lakh_and_no_positions_for_each_book():
    assert BOOKS == ("book1_rules", "book2_hybrid", "book3_ai")  # the names the stories use (epic E)
    for book in BOOKS:
        account = build_paper_account(book)  # the repository's own journal/<book>/account/
        assert account.started and account.starting_cash() == 500_000.0 == STARTING_CASH_RS
        assert account.fills() == [] and len(account.ledger_rows()) == 1
        summary = json.loads(account.file("positions.json").read_text())
        assert summary["open_trades"] == [] and summary["cash_rs"] == 500_000.0 == summary["closed_equity_rs"]
        history = account.equity_history()
        assert [(r["cash_rs"], r["marked_equity_rs"], r["open_trades"]) for r in history] == [
            ("500000.00",) * 2 + ("0",)
        ]


def test_starting_twice_changes_nothing(root):
    folder = account_folder(root, BOOK1_RULES)
    before = {p.name: p.read_bytes() for p in folder.iterdir() if p.name != ".lock"}
    with open_account_writer(BOOK1_RULES, root) as writer:
        assert writer.start(date(2027, 1, 1)) is False
    assert {p.name: p.read_bytes() for p in folder.iterdir() if p.name != ".lock"} == before


def test_the_three_measures_by_hand(root):
    with open_account_writer(BOOK1_RULES, root) as writer:
        assert writer.apply_fill(fill("f1", "spread", "CE25000", "sell", 150.0))  # fills at 149.5
        assert writer.apply_fill(fill("f2", "spread", "CE25200", "buy", 50.0))  # fills at 50.5
    account = build_paper_account(BOOK1_RULES, root)
    sell, buy = account.fills()
    assert sell.amount == pytest.approx(149.5 * 65 - sum(sell.charges.values()))
    assert buy.amount == pytest.approx(-50.5 * 65 - sum(buy.charges.values()))
    state = account.state({"CE25000": Mark(120.0), "CE25200": Mark(40.0, stale=True)}, margin_blocked=30_000)
    cash = 500_000 + sell.amount + buy.amount
    assert state.cash == pytest.approx(cash) and state.closed_equity == 500_000  # nothing closed yet
    assert state.open_value == pytest.approx(-120.0 * 65 + 40.0 * 65)
    assert state.marked_equity == pytest.approx(cash - 120.0 * 65 + 40.0 * 65)  # = cash + marked open value
    assert state.available_cash == pytest.approx(state.marked_equity - 30_000)
    assert state.open_trades == 1 and state.stale_marks == ("CE25200",)
    with pytest.raises(MissingMark, match="CE25200"):
        account.state({"CE25000": Mark(120.0)})  # a price is never invented


def test_a_closed_trade_matches_the_cost_accountants_trade_net(root):
    legs = [("f1", "CE25000", "sell", 150.0), ("f2", "CE25200", "buy", 50.0),
            ("f3", "CE25000", "buy", 120.0), ("f4", "CE25200", "sell", 30.0)]  # fmt: skip
    with open_account_writer(BOOK1_RULES, root) as writer:
        for fill_id, contract, side, price in legs:
            writer.apply_fill(fill(fill_id, "spread", contract, side, price))
        state = writer.record_equity(DAY, {})  # no open trade, so no marks needed
    account = build_paper_account(BOOK1_RULES, root)
    (closed,) = account.closed_trades()
    assert closed.closed_on == DAY
    assert state.closed_equity - 500_000 == pytest.approx(trade_line(closed, CHARGES).net)  # C1 and E1 agree
    assert state.marked_equity == pytest.approx(state.closed_equity) == pytest.approx(state.cash)
    with open_account_writer(BOOK1_RULES, root) as writer, pytest.raises(AccountError, match="closed on"):
        writer.apply_fill(fill("f5", "spread", "CE25000", "sell", 10.0))


def test_a_repeated_fill_id_is_skipped_and_a_reused_one_refused(root):
    with open_account_writer(BOOK1_RULES, root) as writer:
        assert writer.apply_fill(fill("f1", "t", "CE25000", "buy", 100.0)) is True
        assert writer.apply_fill(fill("f1", "t", "CE25000", "buy", 100.0)) is False
        with pytest.raises(AccountError, match="different fill"):
            writer.apply_fill(fill("f1", "t", "CE25000", "buy", 101.0))
    assert [f.fill_id for f in build_paper_account(BOOK1_RULES, root).fills()] == ["f1"]


def test_the_equity_history_keeps_one_row_per_day(root):
    with open_account_writer(BOOK1_RULES, root) as writer:
        writer.apply_fill(fill("f1", "t", "CE25000", "buy", 100.0))
        writer.record_equity(DAY, {"CE25000": Mark(90.0)})
        writer.record_equity(DAY, {"CE25000": Mark(110.0)})
    rows = build_paper_account(BOOK1_RULES, root).equity_history()
    assert [r["date"] for r in rows] == ["2026-10-13"]
    assert float(rows[0]["marked_equity_rs"]) == pytest.approx(float(rows[0]["cash_rs"]) + 110.0 * 65)


def test_writes_need_this_books_lock_held(root, tmp_path_factory):
    account = PaperAccount(root, BOOK1_RULES)
    with pytest.raises(AccountError, match="lock"):
        AccountWriter(account, AccountLock(root, BOOK1_RULES))  # not held
    with AccountLock(root, BOOK2_HYBRID) as other, pytest.raises(AccountError, match="lock"):
        AccountWriter(account, other)  # another book's lock
    elsewhere = tmp_path_factory.mktemp("elsewhere")
    with AccountLock(elsewhere, BOOK1_RULES) as same_name, pytest.raises(AccountError, match="lock"):
        AccountWriter(account, same_name)  # same book name, another folder
    lock = AccountLock(root, BOOK1_RULES)
    with lock:
        writer = AccountWriter(account, lock)
        lease = Lease.from_text(lock.path.read_text())
        assert lease.book == BOOK1_RULES and lease.holder.pid == os.getpid()
    assert lock.path.read_text() == ""  # a clean exit empties the lease
    with pytest.raises(AccountError, match="lock"):
        writer.apply_fill(fill("f1", "t", "CE25000", "buy", 100.0))  # the lock is no longer held


def test_an_account_never_reaches_another_books_files(root):
    account = PaperAccount(root, BOOK1_RULES)
    for name in ("../../book2_hybrid/account/cash_ledger.csv", "..", ".", "", "sub/positions.json", "..\\x"):
        with pytest.raises(BookPathError):
            account.file(name)
    for book in ("book1_rules/../book2_hybrid", "../book2_hybrid", "book4", ""):
        with pytest.raises(BookPathError):
            PaperAccount(root, book)
    linked = os.path.join(root, "journal", BOOK3_AI, "account", "cash_ledger.csv")
    os.remove(linked)
    os.symlink(account_folder(root, BOOK2_HYBRID) / "cash_ledger.csv", linked)  # a file link into another book
    with pytest.raises(BookPathError):
        PaperAccount(root, BOOK3_AI).file("cash_ledger.csv")


def test_an_account_folder_linked_to_another_book_is_refused(tmp_path):
    (tmp_path / "journal" / BOOK2_HYBRID / "account").mkdir(parents=True)
    (tmp_path / "journal" / BOOK1_RULES).mkdir(parents=True)
    os.symlink(tmp_path / "journal" / BOOK2_HYBRID / "account", tmp_path / "journal" / BOOK1_RULES / "account")
    with pytest.raises(BookPathError):
        PaperAccount(tmp_path, BOOK1_RULES).file("positions.json")
    with pytest.raises(BookPathError):
        AccountLock(tmp_path, BOOK1_RULES)


def test_bad_fills_are_refused():
    with pytest.raises(FillError):
        Fill.priced("f1", "t", datetime(2026, 10, 13, 15, 5), "C", Order("buy", 1.0, 65), CHARGES)  # no time zone
    with pytest.raises(FillError):
        fill("f\n1", "t", "C", "buy", 1.0)
    with pytest.raises(FillError):
        fill("f1", "t", "C", "buy", 1.0, units=0)
    with pytest.raises(FillError):
        fill("f1", "t", "C", "hold", 1.0)
