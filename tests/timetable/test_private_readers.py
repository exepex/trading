"""Story E2c criterion 3: after the shared download in a fresh container, each reader of the paper accounts reads the
same values it read from the local folder the run wrote; and each command downloads before it reads anything."""

from datetime import datetime, time

import pytest

from fno import cli
from fno.books.account import PaperAccount
from fno.cards.committed import DownloadedRecords
from fno.cards.status import REGISTRY_PATH, RegistryStatus
from fno.checks.validity_account import LedgerAccounts
from fno.constants import BOOK1_RULES, BOOKS
from fno.desk import wiring as desk_wiring
from fno.desk.pack_store import PackStore
from fno.desk.private_files import PrivateFilesUnavailable, paper_accounts
from fno.desk.records import DeskRecords
from fno.desk.trade_counts import DeskTradeCounts
from fno.market_read_models.home_inputs import BooksReader
from fno.models import IST
from fno.risk.book_view import load_risk_book
from fno.risk.inputs import TradeTerms
from tests.cards.fakes import REGISTRY_HEADER, FakeRecords
from tests.desk.builders import decision_market
from tests.risk.builders import FLY

from .drive_day import fresh_container
from .test_daily_run import NORMAL, run_day
from .test_fills_to_drive import opening_week

TERMS = TradeTerms(FLY, 200, 1)
AFTER = datetime.combine(NORMAL, time(23, 0), IST)


def desk_records(root):
    """E6's scorecards and scoreboard B read the same two things: the accounts named and each one's desk records."""
    records = {name: DeskRecords(PaperAccount(root, name)) for name in paper_accounts(root)}
    return {name: (r.fill_rows(), r.event_rows()) for name, r in records.items()}


READERS = {
    "daily run and E1 (the account itself)": lambda root: PaperAccount(root, BOOK1_RULES).summary(),
    "Book 1: C2's view": lambda root: repr(load_risk_book(root, BOOK1_RULES, decision_market(), {"t1": TERMS})),
    "Book 1: trade counts": lambda root: DeskTradeCounts(DeskRecords(PaperAccount(root, BOOK1_RULES)))._opened(
        "fixture-fly", 1
    ),
    "Book 1: its private pack": lambda root: PackStore(root).private_path(BOOK1_RULES, NORMAL).read_bytes(),
    "C4's ledger facts": lambda root: repr(LedgerAccounts(root).facts(BOOK1_RULES, AFTER)),
    "T1's card": lambda root: (
        RegistryStatus(FakeRecords({REGISTRY_PATH: REGISTRY_HEADER}), DownloadedRecords(root))
        .status(NORMAL)
        .section.lines
    ),
    "E6 and scoreboard B": desk_records,
    "Home": lambda root: BooksReader(root, BOOKS, 2_000_000.0).on(NORMAL),
}


@pytest.mark.parametrize("reader", READERS.values(), ids=READERS.keys())
def test_each_reader_reads_the_same_values_after_the_shared_download(root, tmp_path, alerts, reader):
    run, clock, *_, files = opening_week(root, tmp_path, alerts)
    run_day(run, clock, NORMAL)
    before = reader(root)
    fresh_container(root)
    files.download(NORMAL)
    assert reader(root) == before


COMMANDS = {
    "desk book1": (["desk", "book1", "--day", "2026-10-14"], "fno.books.book1_wiring.build_book1"),
    "desk scorecard": (["desk", "scorecard", "--report-only"], "fno.scorecard.wiring.build_scorecard_run"),
    "scoreboard b": (["scoreboard", "b"], "fno.scoreboard.wiring.build_whole_system_board"),
    "market publish": (["market", "publish"], "fno.market_read_models.wiring.build_market_run"),
    "card daily": (["card", "daily"], "fno.cards.wiring.build_daily_card"),
    "account show": (["account", "show", BOOK1_RULES], "fno.composition.build_paper_account"),
}


@pytest.mark.parametrize("argv, builder", COMMANDS.values(), ids=COMMANDS.keys())
def test_each_command_downloads_before_it_reads(monkeypatch, capsys, argv, builder):
    def unavailable(day=None):
        raise PrivateFilesUnavailable("Drive answered 503")

    monkeypatch.setattr(desk_wiring, "download_private_records", unavailable)
    monkeypatch.setattr(builder, lambda *a, **k: pytest.fail("read before the download"))
    assert cli.main(argv) == 1
    assert capsys.readouterr().out == "stopped: Drive answered 503\n"
