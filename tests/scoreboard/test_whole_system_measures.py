"""Story S6 criteria 7 and 12 on scoreboard B, built from S2's fixture history: every section carries the measures and
the do-nothing comparison, only judged sections the t-check, an empty section has no capital tied, nothing changes
S1's headline or `claim_allowed`, and a rebuild is byte-identical."""

from datetime import date

from fno.books.account import PaperAccount
from fno.composition import build_session_calendar
from fno.constants import BOOK1_RULES, BOOK2_HYBRID
from fno.desk.records import DeskRecords
from fno.risk.open_risk import HeldMaxLoss
from fno.scoreboard.book_trades import NO_RECORD, OVERRIDDEN
from fno.scoreboard.do_nothing import NO_CAPITAL, DoNothing, IndexDay, Terms
from fno.scoreboard.ports import ProtocolStatus
from fno.scoreboard.random_control import RandomControl
from fno.scoreboard.whole_system import canonical
from fno.scoreboard.wiring import board_from
from fno.scorecard.strategy_record import strategy_records
from tests.scorecard.history import CHARGES

from .test_whole_system import MARKS, ON, VERSIONS, history

FLAT = DoNothing(lambda day: IndexDay(20000.0, 1.2), Terms(account_rs=2_000_000.0))
SECTIONS = ("overall", "pilot", "head_to_head", NO_RECORD, OVERRIDDEN)


LUCK = RandomControl(lambda day: None, HeldMaxLoss(CHARGES), CHARGES, 10000.0, 30000.0, {}, runs=10)


def build(root, against=FLAT, luck=LUCK):
    board = board_from(root, CHARGES, build_session_calendar(), VERSIONS, lambda day: MARKS, ProtocolStatus(1, False),
                       120000.0, against, luck)  # fmt: skip
    return board.build(ON)


def test_every_section_carries_the_measures_and_the_do_nothing_comparison(tmp_path):
    book = build(history(tmp_path))["books"][BOOK1_RULES]
    for name in SECTIONS:
        assert {"measures", "do_nothing"} <= set(book[name]), name
    for name, segment in book["head_to_head"]["segments"].items():
        assert {"measures", "do_nothing"} <= set(segment), name
    assert book["head_to_head"]["uncertainty"]["t_check"]["blocks"] == 0
    assert book["pilot"]["uncertainty"] is None  # only judged sections carry the t-check
    assert "random_control" in book["head_to_head"] and "random_control" not in book["pilot"]
    assert all("random_control" in segment for segment in book["head_to_head"]["segments"].values())


def test_an_empty_section_has_no_capital_tied_never_zero_over_zero(tmp_path):
    empty = build(history(tmp_path))["books"][BOOK2_HYBRID][OVERRIDDEN]["do_nothing"]["view_a"]
    assert (empty["reason"], empty["beats_index_after_tax"]) == (NO_CAPITAL, None)


def test_nothing_changes_the_headline_or_the_claim_and_missed_runs_are_listed(tmp_path):
    root = history(tmp_path)
    with_measures, without = build(root), build(root, None)
    for name in ("overall", "head_to_head"):
        a, b = with_measures["books"][BOOK1_RULES][name], without["books"][BOOK1_RULES][name]
        assert a["risk"]["net_per_unit_of_risk"] == b["risk"]["net_per_unit_of_risk"]
        assert a["net_rs"] == b["net_rs"] and a["raw_account_net_rs"] == b["raw_account_net_rs"]
    claim = lambda board: board["books"][BOOK1_RULES]["head_to_head"]["uncertainty"]["claim_allowed"]  # noqa: E731
    assert claim(with_measures) == claim(without)
    assert set(with_measures["missed_runs"]) == set(with_measures["books"])


def test_a_rebuild_is_byte_identical(tmp_path):
    root = history(tmp_path)
    assert canonical(build(root)) == canonical(build(root))


def test_the_drawdown_share_uses_the_books_brake(tmp_path):
    measures = build(history(tmp_path))["books"][BOOK1_RULES]["overall"]["measures"]
    assert measures["max_drawdown_share_of_brake"] == round(measures["max_drawdown_rs"] / 120000.0, 6)
    assert date.fromisoformat(measures["worst_day"]) <= ON


def test_each_strategy_version_entry_reconciles_with_e6s_card(tmp_path):
    root = history(tmp_path)
    board = build(root)
    for book in (BOOK1_RULES, BOOK2_HYBRID):
        cards = {r.strategy: r for r in strategy_records(book, DeskRecords(PaperAccount(root, book)), CHARGES)}
        entries = board["books"][book]["strategies"]
        assert set(entries) == set(cards)
        for version, entry in entries.items():
            card = cards[version]
            assert entry["closed_trade_ids"] == sorted(t.trade_id for t in card.closed), version
            assert entry["closed_net_rs"] == round(sum(t.line.net for t in card.closed), 2), version
            assert {"measures", "do_nothing"} <= set(entry)
