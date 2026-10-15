"""Story P10: Home's F&O blocks publish the books' real accounts and the honest empty picks state, read from the F&O
tool's own records (E1 accounts, the frozen experiment's result, C2's limit); a figure this story does not compute
stops the run with its own reason code rather than publish a wrong one."""

from dataclasses import replace
from datetime import date

import pytest

from fno.books.account import EQUITY_HISTORY_FILE, PaperAccount
from fno.composition import open_account_writer, paper_account_rs
from fno.config import load_app_config
from fno.constants import BOOKS
from fno.desk.private_files import PrivateFiles
from fno.market_read_models import wiring as market_wiring
from fno.market_read_models.home_blocks import FiguresNotComputed, FnoBooksBlock, FnoPicksBlock
from fno.market_read_models.home_inputs import BooksReader, FrozenExperimentApprovals
from fno.market_read_models.wiring import LATEST_FROZEN_EXPERIMENT
from fno.storage.index_store import LocalIndexStore

from .test_market_contract_and_run import CONTRACT, DAY, OPENING_BOOKS, Rows, builder, example_rows, run

EQUITY = "date,cash_rs,closed_equity_rs,marked_equity_rs,open_trades,stale_marks,fills\n"
LEDGER = (
    "entry_id,kind,trade_id,filled_at,contract,side,units,quoted_price,pad,fill_price,brokerage,stt,exchange,sebi,ipft,"
    "stamp,gst,charges_rs,amount_rs,cash_after_rs\nopening,opening_balance,,2026-10-13,,,,,,,,,,,,,,,500000.0,500000.0\n"
)


def journal(tmp_path, rows_by_book: dict[str, str]):
    for book, rows in rows_by_book.items():
        folder = tmp_path / "journal" / book / "account"
        folder.mkdir(parents=True)
        (folder / "cash_ledger.csv").write_text(LEDGER)
        (folder / EQUITY_HISTORY_FILE).write_text(EQUITY + rows)
    return BooksReader(tmp_path, BOOKS, 500_000.0)


def test_each_book_is_read_from_its_own_account_as_of_the_session(tmp_path):
    reader = journal(tmp_path, {
        BOOKS[0]: "2026-10-13,500000,500000,500000,0,,0\n2026-10-14,498000,498000,497250.5,1,,2\n",
        BOOKS[1]: "2026-10-13,500000,500000,500000,0,,0\n",
    })  # fmt: skip
    on_13, on_14 = reader.on(date(2026, 10, 13)), reader.on(date(2026, 10, 14))
    assert [(b.number, b.family, b.value, b.pnl, b.open_trades) for b in on_13] == [
        (1, "rule", 500000.0, 0.0, 0), (2, "hybrid", 500000.0, 0.0, 0), (3, "ai", 500000.0, 0.0, 0),
    ]  # fmt: skip
    assert (on_14[0].value, on_14[0].pnl, on_14[0].open_trades) == (497250.5, -2749.5, 1)  # its own figures only
    assert reader.on(date(2026, 10, 12))[0].value == 500000.0  # before the book opened: its opening balance


def test_the_approvals_are_the_frozen_experiments_passing_policies():
    approvals = FrozenExperimentApprovals(*LATEST_FROZEN_EXPERIMENT)
    assert approvals.passing() == []  # Experiment 1's challenge: "Nothing passed"
    assert approvals.note().startswith("No F&O strategy has passed testing yet: Experiment 1 (the 2019-2023 challenge)")


def test_the_live_wiring_reads_the_books_the_shared_download_brought_and_their_open_risk_cap(monkeypatch, tmp_path):
    """Story E2c: the accounts live in Drive and `market publish` downloads them first (tested in
    `tests/timetable/test_private_readers.py`); here the live wiring reads the books of a checkout filled by that
    download from a fake Drive holding three started accounts."""
    monkeypatch.setattr(market_wiring, "build_versioned_reader", lambda: None)  # no Drive in tests
    seed, checkout, drive = tmp_path / "seed", tmp_path / "checkout", LocalIndexStore(tmp_path / "drive")
    for book in BOOKS:
        with open_account_writer(book, seed) as writer:
            writer.start(DAY)
    PrivateFiles(lambda: drive, seed).move_accounts()
    PrivateFiles(lambda: drive, checkout).download()
    monkeypatch.setattr(market_wiring, "ROOT", checkout)
    home = market_wiring.build_session_rows_builder(load_app_config()).home.on(DAY)
    assert home.limit_max == load_app_config()["risk"]["profiles"]["books"]["open_risk_cap_rs"] == 150000
    assert [b.name for b in home.books] == ["F&O Book 1", "F&O Book 2", "F&O Book 3"] and home.approved == []
    assert all(PaperAccount(checkout, book).started for book in BOOKS)
    assert [b.value for b in home.books] == [paper_account_rs()] * 3


def test_both_blocks_validate_and_say_the_truth():
    rows = example_rows()
    books, picks = FnoBooksBlock().build(rows), FnoPicksBlock().build(rows)
    assert [(b["value"], b["pnl"], b["approved"], b["limit_used"]) for b in books["books"]] == [
        (500000.0, 0.0, [], 0.0)
    ] * 3
    assert books["books"][0]["as_of"] == "2026-10-12T09:30:00Z"  # the books decide at 15:00 IST
    assert picks == {"currency": "INR", "fno_state": {"approved": False, "note": OPENING_BOOKS.approval_note},
                     "rows": [], "baskets": {}}  # fmt: skip
    publication = builder().build(rows)
    for key in ("risk", "today"):
        assert publication.records[key]["payload"] in (books, picks)
    CONTRACT.validate("FnoBooks", books)


@pytest.mark.parametrize(
    "home",
    [
        replace(OPENING_BOOKS, books=[replace(OPENING_BOOKS.books[0], open_trades=1), *OPENING_BOOKS.books[1:]]),
        replace(OPENING_BOOKS, approved=["P3"]),
    ],
)
def test_a_figure_this_story_does_not_compute_stops_the_run_with_its_code(tmp_path, home):
    rows = replace(example_rows(), home=home)
    market, alerts, _ = run(tmp_path, Rows(rows))
    assert market.run(DAY)[0] == 1 and "NOT published (F&O figures)" in alerts.sent[0]
    from fno.market_read_models.run_status import LocalRunStatus

    assert LocalRunStatus(tmp_path, "fno").rows()[0]["reason_code"] == "figures_not_computed"
    with pytest.raises(FiguresNotComputed):
        (FnoBooksBlock() if home.approved == [] else FnoPicksBlock()).build(rows)


def test_the_page_keys_are_the_ones_w10_names_in_the_pinned_schemas():
    """W10's catalog names the read-model pages (judges 61, 63): FnoPicks is page 'today'; FnoBooks is page 'risk'
    (contract 2.5 settled it: scoreboard_b belongs to S2)."""
    picks_source = CONTRACT.schemas["FnoPicks"]["x-catalog"]["source"]
    books_source = CONTRACT.schemas["FnoBooks"]["x-catalog"]["source"]
    assert "page 'today'" in picks_source and FnoPicksBlock.page_key == "today"
    assert "page 'risk'" in books_source and FnoBooksBlock.page_key == "risk"  # 2.5: page risk only


def test_a_top_up_is_capital_never_profit_on_home(tmp_path):
    """Story E1b criterion 6: before the top-up the book's pnl is 0 against Rs 5 lakh; on and after it, 0 against
    Rs 20 lakh; never minus Rs 15 lakh."""
    from datetime import datetime

    from fno.books.account import AccountWriter
    from fno.books.lock import AccountLock
    from fno.models import IST

    for book in BOOKS:
        with AccountLock(tmp_path, book) as lock:
            AccountWriter(PaperAccount(tmp_path, book), lock, 500_000.0).start(date(2026, 10, 13))
    with AccountLock(tmp_path, BOOKS[0]) as lock:
        AccountWriter(PaperAccount(tmp_path, BOOKS[0]), lock, 500_000.0).top_up(
            datetime(2026, 10, 16, 17, 0, tzinfo=IST), 2_000_000.0
        )
    reader = BooksReader(tmp_path, BOOKS, 2_000_000.0)
    figures = {day: reader.on(date(2026, 10, day))[0] for day in (13, 15, 16, 19)}
    assert [(f.value, f.pnl) for f in figures.values()] == [
        (500_000.0, 0.0), (500_000.0, 0.0), (2_000_000.0, 0.0), (2_000_000.0, 0.0)
    ]  # fmt: skip
