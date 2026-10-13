"""Story C2 criterion 7 on real paper accounts (E1): each book is checked with its own account and overrides only."""

from datetime import date, datetime, timedelta

import pytest

from fno.accounting.ledgers import Order
from fno.books.fills import Fill
from fno.books.paths import BookPathError
from fno.composition import open_account_writer
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOKS, SIDE_BUY, SIDE_SELL
from fno.models import IST
from fno.risk.book_view import load_risk_book
from fno.risk.drawdown import DrawdownBrake
from fno.risk.inputs import RiskInputError, TradeTerms
from fno.risk.overrides import brake_restarts, overrides_file
from fno.risk.stress import Shock, StressEngine, stress_positions

from .builders import CHARGES, DAY, FLY, LOT, MODEL, contract, market, proposal, short_fly

START_DAY = date(2026, 9, 1)
EXPIRY = DAY + timedelta(days=14)
LOSER = contract(25000, "CE", EXPIRY)
PRICES = {(25000, "CE"): 150.0, (25000, "PE"): 140.0, (25200, "CE"): 70.0, (24800, "PE"): 60.0}


def _fill(fill_id: str, trade_id: str, name: str, side: str, price: float, day: date) -> Fill:
    when = datetime(day.year, day.month, day.day, 15, 5, tzinfo=IST)
    return Fill.priced(fill_id, trade_id, when, name, Order(side, price, LOT, 0.0), CHARGES)


@pytest.fixture
def root(tmp_path):
    """Book 1 lost Rs 32,500 plus charges on a closed trade (brake hit); book 2 holds an open short fly."""
    for book in BOOKS:
        with open_account_writer(book, tmp_path) as writer:
            writer.start(START_DAY)
    with open_account_writer(BOOK1_RULES, tmp_path) as writer:
        writer.apply_fill(_fill("f1", "loser", LOSER, SIDE_SELL, 100.0, date(2026, 9, 10)))
        writer.apply_fill(_fill("f2", "loser", LOSER, SIDE_BUY, 600.0, date(2026, 9, 20)))
    with open_account_writer(BOOK2_HYBRID, tmp_path) as writer:
        for i, (strike, kind, side) in enumerate(short_fly(25000, 200)):
            price = PRICES[(strike, kind)]
            writer.apply_fill(
                _fill(
                    f"o{i}",
                    "fly",
                    contract(strike, kind, EXPIRY),
                    SIDE_SELL if side < 0 else SIDE_BUY,
                    price,
                    date(2026, 10, 1),
                )
            )
    return tmp_path


def _book(root, name, terms=None):
    return load_risk_book(root, name, market(25000, PRICES, EXPIRY), terms or {})


def _new():
    return proposal("new", FLY, 200, short_fly(25000, 200), EXPIRY)


def test_a_brake_hit_in_one_book_blocks_only_that_book(root):
    book1 = _book(root, BOOK1_RULES)
    book2 = _book(root, BOOK2_HYBRID, {"fly": TradeTerms(FLY, 200, 1)})
    the_market = market(25000, PRICES, EXPIRY)
    assert book1.state.closed_equity < 500_000 - 32_500
    assert not DrawdownBrake(30000).check(_new(), book1, the_market).ok
    assert DrawdownBrake(30000).check(_new(), book2, the_market).ok


def test_a_stress_test_of_one_book_never_includes_another_books_positions(root):
    book1, book3 = _book(root, BOOK1_RULES), _book(root, "book3_ai")
    book2 = _book(root, BOOK2_HYBRID, {"fly": TradeTerms(FLY, 200, 1)})
    assert [p.trade_id for p in stress_positions(book1, _new())] == ["new"]
    assert [p.trade_id for p in stress_positions(book3, None)] == []
    assert [p.trade_id for p in stress_positions(book2, None)] == ["fly"]
    (down,) = StressEngine(MODEL).run(
        stress_positions(book2, None), market(25000, PRICES, EXPIRY), [Shock("d", -8, days=1)]
    )
    assert down.trades[0].loss_from_marks > 0


def test_an_open_trade_without_recorded_terms_is_an_input_error(root):
    with pytest.raises(RiskInputError, match="fly"):
        _book(root, BOOK2_HYBRID)


def test_the_owners_restart_row_reopens_only_its_own_book(root):
    path = overrides_file(root, BOOK1_RULES)
    path.write_text("date,action,reason,entered_by\n2026-10-12,restart_brake,reviewed the loss,owner\n")
    book1 = _book(root, BOOK1_RULES)
    verdict = DrawdownBrake(30000).check(_new(), book1, market(25000, PRICES, EXPIRY))
    assert verdict.ok and verdict.numbers["restarted_on"] == "2026-10-12"
    assert verdict.numbers["brake_level_rs"] == pytest.approx(book1.state.closed_equity - 30000)
    assert brake_restarts(root, BOOK2_HYBRID, DAY) == ()


def test_a_restart_dated_after_the_decision_day_is_not_yet_in_force(root):
    overrides_file(root, BOOK1_RULES).write_text("date,action,reason,entered_by\n2026-10-14,restart_brake,r,owner\n")
    assert brake_restarts(root, BOOK1_RULES, DAY) == ()


@pytest.mark.parametrize(
    "text",
    [
        "date,action,reason\n2026-10-12,restart_brake,r\n",
        "date,action,reason,entered_by\n2026-10-12,reset,r,owner\n",
        "date,action,reason,entered_by\n2026-10-12,restart_brake,,owner\n",
        "date,action,reason,entered_by\n12/10/2026,restart_brake,r,owner\n",
    ],
)
def test_a_malformed_override_row_is_an_input_error(root, text):
    overrides_file(root, BOOK1_RULES).write_text(text)
    with pytest.raises(RiskInputError):
        brake_restarts(root, BOOK1_RULES, DAY)


def test_overrides_are_read_only_from_a_known_books_own_folder(root):
    with pytest.raises(BookPathError):
        overrides_file(root, "../book2_hybrid")
    assert overrides_file(root, BOOK1_RULES) == root / "journal" / BOOK1_RULES / "owner_overrides.csv"
