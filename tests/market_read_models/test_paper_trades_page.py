"""Story P2c (screen W3c): the `paper_trades` page from each book's own paper account (E1, Drive only), its desk
records (E4), the playbook registry and C5's published limits. Criterion 1 (every number re-read from the account,
C1's trade line and the config), 2 (a planted Drive value reaches no file and no message), 3 (in
test_contract_log_line.py) and 4 (never a version tag, a strike rule or anything outside the contract's fields)."""

import csv
import json
from datetime import date, datetime

import pytest

from fno.accounting.ledgers import Order, trade_line
from fno.books.account import AccountWriter, PaperAccount
from fno.books.equity import trade_positions
from fno.books.fills import Fill
from fno.books.lock import AccountLock
from fno.config import load_app_config
from fno.constants import BOOKS, RISK_PROFILE_BOOKS
from fno.desk.records import EVENT_COLUMNS, EVENTS_FILE, FILL_COLUMNS, FILLS_FILE
from fno.market_read_models.blocks import SessionRows
from fno.market_read_models.paper_trades_block import FnoPaperTradesBlock
from fno.market_read_models.paper_trades_closed import ClosedTrades
from fno.market_read_models.paper_trades_inputs import PaperBooksReader
from fno.market_read_models.publication import PublicationBuilder
from fno.market_read_models.wiring import build_pinned_contract
from fno.models import IST
from fno.risk.profile_settings import profile_settings

CONTRACT_SCHEMAS = build_pinned_contract().schemas

CFG = load_app_config()
PROFILE = profile_settings(CFG, RISK_PROFILE_BOOKS)
OPENED, TOPPED_UP, DAY = date(2026, 10, 13), date(2026, 10, 15), date(2026, 10, 16)
PLANTED = 1_234_567.89  # a value only the Drive account holds
REGISTRY = "name,version,sha256,status,changed_on,approved_by,evidence_commit\n" + "".join(
    f"{n},1,{'a' * 64},shadow,2026-10-01,owner,{'b' * 40}\n" for n in ("iv-rich-no-event-fly", "calm-condor")
)  # two strategies whose names spell their filters: k is 1 and 2, never the name
STRUCTURES = {("book2_hybrid", DAY, "d1"): "SF"}


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


def reader(root) -> PaperBooksReader:
    closed = ClosedTrades(
        lambda: REGISTRY, lambda book, day, decision: STRUCTURES.get((book, day, decision), ""), CFG["charges"]
    )
    return PaperBooksReader(root, BOOKS, PROFILE, closed)


def published(root, day=DAY) -> dict:
    rows = SessionRows(day, [], [], [], [], paper_trades=reader(root).on(day))
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


def fill(book_root, book, fill_id, trade_id, side, price, hour, day=DAY):
    when = datetime(day.year, day.month, day.day, hour, 0, tzinfo=IST)
    order = Order(side, price, 65, 0.0)
    write(
        book_root, book, lambda w: w.apply_fill(Fill.priced(fill_id, trade_id, when, CONTRACT, order, CFG["charges"]))
    )


def desk_rows(root, book, name, rows, columns):
    """The desk's own record files (E4), written in their real columns (blank where this test needs nothing)."""
    path = PaperAccount(root, book).file(name)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        out = csv.DictWriter(fh, fieldnames=columns)
        out.writeheader()
        out.writerows([dict.fromkeys(columns, "") | r for r in rows])


CONTRACT = "NIFTY26102725000CE"


def closed_trade(root, sell_back=2_150.0, reason="profit_target: the net if closed now reaches the profit target"):
    """Book 2: bought at 2,100 at 10:00 and sold back at 11:00 on 16 Oct, under the registry's first strategy."""
    fill(root, BOOKS[1], "f1", "t1", "buy", 2_100.0, 10)
    fill(root, BOOKS[1], "f2", "t1", "sell", sell_back, 11)
    base = {"book": BOOKS[1], "strategy": "iv-rich-no-event-fly-v1", "decision_id": "d1", "trade_id": "t1"}
    desk_rows(root, BOOKS[1], FILLS_FILE, [base | {"fill_id": "f1", "action": "open"},
                                           base | {"fill_id": "f2", "action": "close"}], FILL_COLUMNS)  # fmt: skip
    desk_rows(root, BOOKS[1], EVENTS_FILE, [base | {"event_id": "e1", "outcome": "exit_ordered", "reason": reason}],
              EVENT_COLUMNS)  # fmt: skip


def test_a_closed_trade_is_c1s_trade_line_under_a_registry_label_never_its_version_tag(root):
    closed_trade(root)
    (trade,) = published(root)["closed"]
    position = trade_positions(PaperAccount(root, BOOKS[1]).fills())["t1"]
    line = trade_line(position.as_ledger_trade(), dict(CFG["charges"]))
    assert (trade["gross"], trade["net"]) == (round(line.gross, 2), round(line.net, 2))
    assert trade["costs"] == round(line.pads + sum(line.charges.values()), 2) and trade["costs"] > 0
    assert trade["result"] == ("won" if line.net > 0 else "lost") and trade["fills"] is None
    assert (trade["family"], trade["strategy"], trade["structure"]) == (
        "hybrid",
        "Strategy 1, version 1",
        "sold iron butterfly",
    )
    assert (trade["opened_on"], trade["closed_on"], trade["exit"]) == ("2026-10-16", "2026-10-16", "take_profit")
    text = json.dumps(published(root))
    assert "iv-rich" not in text and "no-event" not in text  # the tag names the strategy's filters


@pytest.mark.parametrize(
    ("reason", "exit_kind"),
    [("stop_loss: the net if closed now reaches the stop loss", "max_loss_exit"),
     ("time_exit: 2026-10-16 is on or after 2026-10-16 (D2)", "time_exit"), ("protection unverified", "other")],
)  # fmt: skip
def test_the_exit_is_the_desks_own_rule_name(root, reason, exit_kind):
    closed_trade(root, reason=reason)
    assert published(root)["closed"][0]["exit"] == exit_kind


def held(root, day=DAY) -> str | None:
    """Story P11: the reason the page is held today (None: built), after the publication left out only this page."""
    inputs = reader(root).on(day)
    rows = SessionRows(day, [], [], [], [], paper_trades=inputs)
    publication = PublicationBuilder([FnoPaperTradesBlock()], build_pinned_contract(), "c" * 40).build(rows)
    assert ("paper_trades" in publication.records) == (inputs.held is None)  # no earlier page here: no row
    assert publication.held == ({"paper_trades": inputs.held} if inputs.held else {})
    return inputs.held


def test_an_open_trade_holds_only_this_page_with_a_fixed_reason_never_an_amount_or_a_book(root):
    fill(root, BOOKS[1], "f1", "t1", "buy", PLANTED, 10)
    reason = held(root)
    assert reason == "A book holds an open trade, and this page cannot mark it for the session yet"  # the agreed one
    assert held(root, date(2026, 10, 15)) is None  # the session before still builds


def test_a_strategy_with_no_registry_row_or_no_known_structure_holds_the_page(root):
    closed_trade(root)
    STRUCTURES[("book2_hybrid", DAY, "d1")] = "XX"
    try:
        assert "no committed decision record naming a known structure" in held(root)
    finally:
        STRUCTURES[("book2_hybrid", DAY, "d1")] = "SF"
    closed = ClosedTrades(lambda: "name,version\n", lambda *_: "SF", CFG["charges"])
    assert "no row in the playbook registry" in PaperBooksReader(root, BOOKS, PROFILE, closed).on(DAY).held


def test_a_shadow_is_its_own_card_under_a_registry_label(root):
    write(root, "shadow:calm-condor-v3", lambda w: w.start(OPENED), opening=2_000_000.0)
    (shadow,) = published(root)["shadows"]
    assert shadow == {"name": "Strategy 2, version 3", "label": "shadow", "as_of": "2026-10-13",
                      "opening_value": 2_000_000.0, "value": 2_000_000.0, "open_trades": 0}  # fmt: skip
    write(root, "shadow:unknown-v1", lambda w: w.start(OPENED), opening=2_000_000.0)
    assert "no row in the playbook registry" in held(root)


def test_every_hold_reason_of_the_page_matches_the_pinned_pattern():
    import re

    from fno.market_read_models import paper_trades_closed, paper_trades_inputs

    pattern = CONTRACT_SCHEMAS["FnoPageHolds"]["properties"]["holds"]["items"]["properties"]["reason"]["pattern"]
    for reason in (paper_trades_inputs.OPEN_NOT_BUILT, paper_trades_inputs.BRAKE_UNREADABLE,
                   paper_trades_closed.NOT_IN_REGISTRY, paper_trades_closed.NO_STRUCTURE):  # fmt: skip
        assert re.fullmatch(pattern, reason), reason


def test_a_planted_drive_value_reaches_the_payload_only_never_a_file(root):
    write(root, BOOKS[0], lambda w: w.top_up(datetime(2026, 10, 16, 8, 0, tzinfo=IST), PLANTED + 2_000_000.0))
    before = sorted(p for p in root.rglob("*") if p.is_file())
    page = published(root)
    assert page["accounts"][0]["opening_value"] == PLANTED + 2_000_000.0  # read from the account, in memory
    assert sorted(p for p in root.rglob("*") if p.is_file()) == before  # the build wrote nothing
    assert set(json.loads(json.dumps(page))) == {"accounts", "shadows", "open", "closed"}


def test_a_losing_closed_trade_moves_the_brake_by_exactly_its_net_loss(root):
    closed_trade(root, sell_back=1_000.0)  # bought at 2,100: about Rs 71,500 lost before costs
    page = published(root)
    (trade,) = page["closed"]
    assert trade["result"] == "lost" and page["accounts"][1]["brake"]["loss_from_high"] == round(-trade["net"], 2)
    assert page["accounts"][0]["brake"]["loss_from_high"] == 0.0  # each book's brake is its own


def test_a_held_paper_books_page_leaves_every_other_page_published(tmp_path):
    """Judge 248: a book's open trade holds only `paper_trades`; the run publishes every other page and alerts once."""
    from dataclasses import replace

    from fno.market_read_models.paper_trades_inputs import OPEN_NOT_BUILT
    from fno.market_read_models.wiring import build_market_blocks

    from .test_market_contract_and_run import DAY as RUN_DAY
    from .test_market_contract_and_run import Rows, example_rows, run

    good = example_rows()
    rows = replace(good, paper_trades=replace(good.paper_trades, held=OPEN_NOT_BUILT))
    market, alerts, publisher = run(tmp_path, Rows(rows))
    code, _ = market.run(RUN_DAY)
    pages = {key for b in build_market_blocks() for key in b.pages(good)}
    assert code == 0 and set(publisher.current()) == pages - {"paper_trades"} | {"page_holds"}
    assert alerts.sent == [f"{RUN_DAY}: paper_trades held back: {OPEN_NOT_BUILT}"]
