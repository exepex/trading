"""Story E1b criterion 5: C4 reads the same ledger as E1 and C2 on its own and agrees with C2 on capital, cash and the
brake's series at the same cutoff. A top-up written after the cutoff never counts, and a top-up row between two fills
is capital, never a fill."""

from datetime import date, datetime

import pytest

from fno.accounting.ledgers import Order
from fno.books.account import AccountWriter, PaperAccount
from fno.books.fills import Fill
from fno.books.lock import AccountLock
from fno.checks.validity_account import LedgerAccounts
from fno.checks.validity_caps import paper_account_check
from fno.config import ROOT, load_config
from fno.constants import BOOK1_RULES
from fno.models import IST
from fno.risk.book_view import load_risk_book
from tests.risk.builders import market

CHARGES = load_config(ROOT / "config.yaml")["charges"]
T, NEXT, EXPIRY = date(2026, 10, 16), date(2026, 10, 19), date(2026, 10, 27)
SIZE = 2_000_000.0


def _ist(day, hour, minute=0):
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=IST)


def _write(root, action):
    with AccountLock(root, BOOK1_RULES) as lock:
        return action(AccountWriter(PaperAccount(root, BOOK1_RULES), lock, 500_000.0))


def _fill(fill_id, trade, side, price, when):
    return Fill.priced(fill_id, trade, when, "NIFTY26102725000CE", Order(side, price, 65, 0.0), CHARGES)


@pytest.fixture
def root(tmp_path):
    """Opened 13 Oct with Rs 5 lakh; trade t1 bought on 14 Oct and sold on 15 Oct; the top-up at 17:00 on 16 Oct; trade
    t2 bought and sold on 19 Oct before 15:00: the top-up row sits between fills."""
    fills = [
        ("b1", "t1", "buy", 200.0, _ist(date(2026, 10, 14), 15, 15)),
        ("s1", "t1", "sell", 150.0, _ist(date(2026, 10, 15), 15, 15)),
    ]
    _write(tmp_path, lambda w: w.start(date(2026, 10, 13)))
    for fill in fills:
        _write(tmp_path, lambda w, fill=fill: w.apply_fill(_fill(*fill)))
    _write(tmp_path, lambda w: w.top_up(_ist(T, 17), SIZE))
    for fill in (("b2", "t2", "buy", 100.0, _ist(NEXT, 10)), ("s2", "t2", "sell", 100.0, _ist(NEXT, 11))):
        _write(tmp_path, lambda w, fill=fill: w.apply_fill(_fill(*fill)))
    return tmp_path


@pytest.mark.parametrize(("day", "capital"), [(T, 500_000.0), (NEXT, SIZE)])
def test_c4_and_c2_agree_on_capital_cash_and_the_series_at_the_cutoff(root, day, capital):
    facts = LedgerAccounts(root).facts(BOOK1_RULES, _ist(day, 15))
    c2 = load_risk_book(root, BOOK1_RULES, market(25000, {}, EXPIRY, day=day), {})
    assert facts.closed_equity[0][1] == capital == c2.state.capital == c2.closed_equity[0][1]
    assert paper_account_check(facts, SIZE).ok is (capital == SIZE)
    if day == NEXT:  # every fill before the cutoff (C2 reads the whole ledger; C4 only rows by its cutoff)
        assert [(d, round(v, 6)) for d, v in facts.closed_equity] == [(d, round(v, 6)) for d, v in c2.closed_equity]
        assert facts.cash == pytest.approx(c2.state.cash) and facts.positions == ()


def test_a_top_up_row_between_two_fills_is_capital_never_a_fill(root):
    facts = LedgerAccounts(root).facts(BOOK1_RULES, _ist(NEXT, 15))
    loss = SIZE - facts.closed_equity[-1][1]
    assert 3_250 < loss < 3_700  # (200 - 150) x 65 plus both trades' charges: the top-up is not in any trade
    assert [trade for trade, _ in facts.session] == ["t2"] and facts.positions == ()
