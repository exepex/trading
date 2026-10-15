"""Story E1b criterion 4: in C2, a top-up is capital. The paper-account rule passes once a book's capital is the books'
size, the drawdown brake never moves (it measures drawdown of profit and loss), and a top-up written after a
decision's cutoff never counts for that decision, live or in a replay."""

from datetime import date, datetime

import pytest

from fno.accounting.ledgers import Order
from fno.books.account import AccountWriter, PaperAccount
from fno.books.fills import Fill
from fno.books.lock import AccountLock
from fno.config import ROOT, load_config
from fno.constants import BOOK1_RULES
from fno.models import IST
from fno.risk.book_view import load_risk_book
from fno.risk.caps import PaperAccountSize
from fno.risk.drawdown import DrawdownBrake

from .builders import FLY, market, proposal, short_fly

CHARGES = load_config(ROOT / "config.yaml")["charges"]
OPENED, T, NEXT = date(2026, 10, 13), date(2026, 10, 16), date(2026, 10, 19)
EXPIRY = date(2026, 10, 27)
NEW = proposal("new", FLY, 200, short_fly(25000, 200), EXPIRY)
SIZE, BRAKE = 2_000_000.0, 120_000.0


def _ist(day, hour):
    return datetime(day.year, day.month, day.day, hour, 0, tzinfo=IST)


def _write(root, action):
    with AccountLock(root, BOOK1_RULES) as lock:
        return action(AccountWriter(PaperAccount(root, BOOK1_RULES), lock, 500_000.0))


def _book(root, day):
    return load_risk_book(root, BOOK1_RULES, market(25000, {}, EXPIRY, day=day), {})


def _lose(root, sell_back: float):
    """A closed call trade on 14 Oct: bought at 2,100.00, sold at `sell_back` (no pad), 65 units."""
    contract = "NIFTY26102725000CE"
    for fill_id, side, price, hour in (("b", "buy", 2100.0, 10), ("s", "sell", sell_back, 11)):
        when = _ist(date(2026, 10, 14), hour)
        fill = Fill.priced(fill_id, "loser", when, contract, Order(side, price, 65, 0.0), CHARGES)
        _write(root, lambda w, fill=fill: w.apply_fill(fill))


@pytest.fixture
def root(tmp_path):
    _write(tmp_path, lambda w: w.start(OPENED))
    return tmp_path


def test_the_paper_account_rule_follows_capital_at_the_decision_cutoff(root):
    rule = PaperAccountSize(SIZE)
    assert not rule.check(NEW, _book(root, T), None).ok  # Rs 5 lakh: refused
    _write(root, lambda w: w.top_up(_ist(T, 17), SIZE))
    assert not rule.check(NEW, _book(root, T), None).ok  # T's 15:00 decision, replayed after the 17:00 top-up
    assert rule.check(NEW, _book(root, NEXT), None).ok  # the next session sees Rs 20 lakh


@pytest.mark.parametrize("sell_back", [100.0, 50.0])
def test_a_top_up_never_lifts_or_moves_the_brake(root, sell_back):
    """About Rs 1.3 lakh lost before the top-up: braked before and still braked after, by the same drawdown."""
    _lose(root, sell_back)
    before = DrawdownBrake(BRAKE).check(NEW, _book(root, NEXT), None)
    _write(root, lambda w: w.top_up(_ist(T, 10), SIZE))
    after = DrawdownBrake(BRAKE).check(NEW, _book(root, NEXT), None)
    assert not before.ok and not after.ok
    assert before.numbers["drawdown_rs"] > BRAKE
    assert after.numbers["drawdown_rs"] == pytest.approx(before.numbers["drawdown_rs"])
    assert after.numbers["high_water_mark_rs"] == pytest.approx(SIZE)  # the capital, never a capital step


@pytest.mark.parametrize(("loss", "ok"), [(119_000.0, True), (121_000.0, False)])  # charges add under Rs 1,000
def test_the_brake_boundary_is_the_same_after_a_top_up(root, loss, ok):
    """Just under and just over the Rs 1.2 lakh brake, measured on profit and loss whatever the capital."""
    sell_back = 2100.0 - loss / 65  # charges add a little loss; checked against the reported drawdown below
    _lose(root, sell_back)
    _write(root, lambda w: w.top_up(_ist(T, 10), SIZE))
    verdict = DrawdownBrake(BRAKE).check(NEW, _book(root, NEXT), None)
    drawdown = verdict.numbers["drawdown_rs"]
    assert verdict.ok is ok and loss < drawdown < loss + 1_000
    assert verdict.numbers["closed_equity_rs"] == pytest.approx(SIZE - drawdown)


def test_a_book_at_its_high_gets_no_higher_high_from_a_top_up(root):
    _write(root, lambda w: w.top_up(_ist(T, 10), SIZE))
    verdict = DrawdownBrake(BRAKE).check(NEW, _book(root, NEXT), None)
    assert verdict.ok and verdict.numbers["drawdown_rs"] == 0.0 and verdict.numbers["high_water_mark_rs"] == SIZE
