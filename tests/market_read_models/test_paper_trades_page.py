"""Story P2c (screen W3c): the `paper_trades` page from each book's own paper account (E1, Drive only) and C5's
published limits. Criterion 1 (every number re-read from the account and the config), 2 (a planted Drive value
reaches no file and no message), 3 (in test_contract_log_line.py) and 4 (nothing but the contract's fields)."""

import json
from datetime import date, datetime

import pytest

from fno.accounting.ledgers import Order
from fno.books.account import AccountWriter, PaperAccount
from fno.books.fills import Fill
from fno.books.lock import AccountLock
from fno.config import load_app_config
from fno.constants import BOOKS, RISK_PROFILE_BOOKS
from fno.market_read_models.blocks import SessionRows
from fno.market_read_models.home_blocks import FiguresNotComputed
from fno.market_read_models.paper_trades_block import FnoPaperTradesBlock
from fno.market_read_models.paper_trades_inputs import PaperBooksReader
from fno.market_read_models.publication import PublicationBuilder
from fno.market_read_models.wiring import build_pinned_contract
from fno.models import IST
from fno.risk.profile_settings import profile_settings

CFG = load_app_config()
PROFILE = profile_settings(CFG, RISK_PROFILE_BOOKS)
OPENED, TOPPED_UP, DAY = date(2026, 10, 13), date(2026, 10, 15), date(2026, 10, 16)
PLANTED = 1_234_567.89  # a value only the Drive account holds


def write(root, book, action, opening=500_000.0):
    with AccountLock(root, book) as lock:
        return action(AccountWriter(PaperAccount(root, book), lock, opening))


@pytest.fixture
def root(tmp_path):
    """The three books as the committed daily totals show them: opened on 13 Oct, topped up to Rs 20 lakh on 15 Oct."""
    for book in BOOKS:
        write(tmp_path, book, lambda w: w.start(OPENED))
        write(tmp_path, book, lambda w: w.top_up(datetime(2026, 10, 15, 17, 0, tzinfo=IST), 2_000_000.0))
    return tmp_path


def published(root, day=DAY) -> dict:
    rows = SessionRows(day, [], [], [], [], paper_trades=PaperBooksReader(root, BOOKS, PROFILE).on(day))
    builder = PublicationBuilder([FnoPaperTradesBlock()], build_pinned_contract(), "c" * 40)
    return builder.build(rows).records["paper_trades"]["payload"]


def test_each_book_is_its_own_account_and_the_limits_are_the_c5_profiles(root):
    page = published(root)
    assert [a["family"] for a in page["accounts"]] == ["rule", "hybrid", "ai"]
    for book, account in zip(BOOKS, page["accounts"], strict=True):
        last = PaperAccount(root, book).equity_history()[-1]
        assert (account["as_of"], account["value"], account["cash"], account["open_trades"]) == (
            last["date"], float(last["marked_equity_rs"]), float(last["cash_rs"]), int(last["open_trades"])
        )  # fmt: skip
        assert account["opening_value"] == PaperAccount(root, book).capital() == 2_000_000.0
        assert (
            account["open_risk_cap"] == PROFILE.open_risk_cap_rs == CFG["risk"]["profiles"]["books"]["open_risk_cap_rs"]
        )
        assert account["brake"] == {"loss_from_high": 0.0, "pause_at": PROFILE.drawdown_brake_rs}
        assert account["open_max_loss"] == 0.0
    assert (page["shadows"], page["open"], page["closed"]) == ([], [], [])


def test_a_session_before_the_top_up_shows_the_capital_then_in_force(root):
    page = published(root, date(2026, 10, 14))
    assert {a["opening_value"] for a in page["accounts"]} == {500_000.0}
    assert {a["as_of"] for a in page["accounts"]} == {"2026-10-13"}


def test_a_book_not_opened_yet_shows_its_opening_balance_from_config(tmp_path):
    page = published(tmp_path, date(2026, 10, 12))
    assert {(a["opening_value"], a["value"], a["cash"]) for a in page["accounts"]} == {(PROFILE.paper_account_rs,) * 3}


def test_a_trade_stops_the_page_named_by_book_and_count_never_an_amount(root):
    when = datetime(2026, 10, 16, 10, 0, tzinfo=IST)
    fill = Fill.priced("f1", "t1", when, "NIFTY26102725000CE", Order("buy", PLANTED, 65, 0.0), CFG["charges"])
    write(root, BOOKS[1], lambda w: w.apply_fill(fill))
    with pytest.raises(FiguresNotComputed) as stopped:
        published(root)
    assert str(stopped.value).startswith("book2_hybrid: 1 paper trade(s) on record")
    assert "1234567" not in str(stopped.value) and "1,234,567" not in str(stopped.value)
    assert published(root, date(2026, 10, 15))["accounts"][1]["open_trades"] == 0  # the session before it still builds


def test_a_shadow_account_stops_the_page_named(root):
    (root / "journal" / "shadow" / "calm-fly-v1" / "account").mkdir(parents=True)
    with pytest.raises(FiguresNotComputed, match="1 shadow account"):
        published(root)


def test_a_planted_drive_value_reaches_the_payload_only_never_a_file(root):
    write(root, BOOKS[0], lambda w: w.top_up(datetime(2026, 10, 16, 8, 0, tzinfo=IST), PLANTED + 2_000_000.0))
    before = sorted(p for p in root.rglob("*") if p.is_file())
    page = published(root)
    assert page["accounts"][0]["opening_value"] == PLANTED + 2_000_000.0  # read from the account, in memory
    assert sorted(p for p in root.rglob("*") if p.is_file()) == before  # the build wrote nothing
    assert set(json.loads(json.dumps(page))) == {"accounts", "shadows", "open", "closed"}
