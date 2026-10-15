"""Story E1b criteria 1-3, 8 and 9: a capital top-up appended at its write instant, its refusals, capital at an instant
(never a trade, a fill or profit), the command, and the book firewall."""

from datetime import date, datetime

import pytest

from fno.accounting.ledgers import Order
from fno.books.account import AccountError, AccountWriter, PaperAccount
from fno.books.cli import top_up_books
from fno.books.equity import trade_positions
from fno.books.fills import Fill
from fno.books.lock import AccountLock
from fno.config import ROOT, load_config
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOKS, LEDGER_TOP_UP
from fno.models import IST

CHARGES = load_config(ROOT / "config.yaml")["charges"]
OPENED = date(2026, 10, 13)
T = date(2026, 10, 16)
TARGET = 2_000_000.0


def at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=IST)


def _write(root, book, action, opening=500_000.0):
    with AccountLock(root, book) as lock:
        return action(AccountWriter(PaperAccount(root, book), lock, opening))


def _fill(fill_id, trade, side, price, when):
    return Fill.priced(fill_id, trade, when, "NIFTY26102725000CE", Order(side, price, 65, 0.0), CHARGES)


@pytest.fixture
def root(tmp_path):
    """The three books as committed: opened on 13 Oct with Rs 5 lakh, no fill."""
    for book in BOOKS:
        _write(tmp_path, book, lambda writer: writer.start(OPENED))
    return tmp_path


def _ledger(root, book=BOOK1_RULES) -> bytes:
    return PaperAccount(root, book).file("cash_ledger.csv").read_bytes()


def test_a_top_up_appends_one_row_at_its_write_instant_and_changes_nothing_before(root):
    before = _ledger(root)
    done = _write(root, BOOK1_RULES, lambda w: w.top_up(at(T, 17), TARGET))
    after = _ledger(root)
    assert done.amount == 1_500_000.0 and not done.further
    assert after.startswith(before)  # every earlier row byte-for-byte
    row = PaperAccount(root, BOOK1_RULES).ledger_rows()[-1]
    assert row["kind"] == LEDGER_TOP_UP and row["entry_id"] == "top_up_2026-10-16"
    assert row["filled_at"] == "2026-10-16T17:00:00+05:30"
    assert float(row["amount_rs"]) == 1_500_000.0 and float(row["cash_after_rs"]) == 2_000_000.0


def test_the_amount_restores_capital_not_equity(root):
    """A book with a realised loss still gets Rs 15 lakh and keeps its loss."""

    def lose(writer):
        writer.apply_fill(_fill("f1", "t", "buy", 200.0, at(OPENED, 15, 15)))
        writer.apply_fill(_fill("f2", "t", "sell", 50.0, at(OPENED, 15, 20)))

    _write(root, BOOK1_RULES, lose)
    account = PaperAccount(root, BOOK1_RULES)
    loss = 500_000.0 - account.state({}).closed_equity
    assert loss > 9_750
    assert _write(root, BOOK1_RULES, lambda w: w.top_up(at(T, 17), TARGET)).amount == 1_500_000.0
    state = account.state({})
    assert account.capital() == TARGET and state.closed_equity == pytest.approx(TARGET - loss)


@pytest.mark.parametrize(
    ("setup", "problem"),
    [
        ("above", "above"),
        ("open", "open position"),
    ],
)
def test_a_top_up_is_refused_with_its_reason_and_nothing_written(root, setup, problem):
    if setup == "above":
        _write(root, BOOK1_RULES, lambda w: w.top_up(at(T, 10), 2_500_000.0))
    else:
        _write(root, BOOK1_RULES, lambda w: w.apply_fill(_fill("f1", "t", "buy", 200.0, at(OPENED, 15, 15))))
    before = _ledger(root)
    with pytest.raises(AccountError, match=problem):
        _write(root, BOOK1_RULES, lambda w: w.top_up(at(T, 17), TARGET))
    assert _ledger(root) == before


def test_a_book_at_size_is_left_unchanged_and_a_not_started_book_is_refused(root, tmp_path_factory):
    _write(root, BOOK1_RULES, lambda w: w.top_up(at(T, 17), TARGET))
    before = _ledger(root)
    assert _write(root, BOOK1_RULES, lambda w: w.top_up(at(T, 18), TARGET)).amount == 0.0  # a second run
    assert _ledger(root) == before
    empty = tmp_path_factory.mktemp("empty")
    with pytest.raises(AccountError, match="not been started"):
        _write(empty, BOOK1_RULES, lambda w: w.top_up(at(T, 17), TARGET))


def test_a_top_up_needs_this_books_lock(root):
    account = PaperAccount(root, BOOK1_RULES)
    lock = AccountLock(root, BOOK1_RULES)
    with lock:
        writer = AccountWriter(account, lock, 500_000.0)
    with pytest.raises(AccountError, match="lock"):
        writer.top_up(at(T, 17), TARGET)  # the lock is no longer held


@pytest.mark.parametrize(
    ("written", "decision", "capital"),
    [
        (at(T, 17), at(T, 15), 500_000.0),  # after the 15:00 decision: not capital for it, live or replayed
        (at(T, 17), at(date(2026, 10, 19), 15), 2_000_000.0),  # the next session's decision
        (at(T, 10), at(T, 15), 2_000_000.0),  # before the decision: counts
    ],
)
def test_capital_counts_a_top_up_only_from_its_write_instant(root, written, decision, capital):
    _write(root, BOOK1_RULES, lambda w: w.top_up(written, TARGET))
    account = PaperAccount(root, BOOK1_RULES)
    assert account.capital(decision) == capital and account.state({}, at=decision).capital == capital


def test_a_top_up_is_never_a_fill_a_trade_or_a_c1_ledger_line(root):
    _write(root, BOOK1_RULES, lambda w: w.top_up(at(T, 17), TARGET))
    account = PaperAccount(root, BOOK1_RULES)
    assert account.fills() == [] and trade_positions(account.fills()) == {} and account.closed_trades() == []
    summary = account.summary()
    assert summary["capital_rs"] == TARGET == summary["cash_rs"] == summary["closed_equity_rs"]
    assert summary["open_trades"] == []
    (row,) = [r for r in account.equity_history() if r["date"] == T.isoformat()]
    assert float(row["marked_equity_rs"]) == TARGET  # the day's equity row is written


def test_the_command_tops_up_each_book_once_and_names_a_further_top_up(root, capsys, monkeypatch):
    import fno.composition as composition

    assert top_up_books(BOOKS, root) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3 and all("topped up by Rs 1,500,000.00" in line for line in lines)
    assert top_up_books(BOOKS, root) == 0
    assert all("already at size" in line for line in capsys.readouterr().out.splitlines())
    monkeypatch.setattr(composition, "paper_account_rs", lambda: 2_500_000.0)  # a raised target: an owner decision
    assert top_up_books([BOOK1_RULES], root) == 0
    assert "a further top-up by Rs 500,000.00" in capsys.readouterr().out


def test_the_command_reports_a_refused_book_and_exits_non_zero(root, capsys):
    _write(root, BOOK1_RULES, lambda w: w.apply_fill(_fill("f1", "t", "buy", 200.0, at(OPENED, 15, 15))))
    assert top_up_books(BOOKS, root) == 1
    out = capsys.readouterr().out
    assert f"{BOOK1_RULES}: refused" in out and f"{BOOK2_HYBRID}: topped up" in out


def test_a_top_up_never_touches_another_books_files(root):
    others = {b: _ledger(root, b) for b in BOOKS if b != BOOK1_RULES}
    _write(root, BOOK1_RULES, lambda w: w.top_up(at(T, 17), TARGET))
    assert {b: _ledger(root, b) for b in others} == others
