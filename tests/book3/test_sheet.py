"""Story F6 criterion 13 (the gap found 25 Oct: no `BookSheet` for Book 3 was registered, so its private pack would
hold no `evaluation` and the decider would refuse every day): Book 3's sheet is registered in the pack step's
`SHEETS`, built on first use inside the per-book guard, gives D2's evaluation with each common opportunity's widths,
and is the sheet the decider reproduces, so a pick on it trades."""

from datetime import time

from fno.book3.sheet import common_widths
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI
from fno.desk.book_sheet import LazySheet
from fno.desk.common_pack import CommonPack
from fno.desk.pack_store import PackStore
from fno.desk.pack_wiring import SHEETS, book_sheets
from fno.desk.packs import SHEET_REFUSED, WrittenPacks
from fno.desk.private_pack import PrivatePackBuilder
from tests.book3.engine_builders import (
    COMMON_OPPORTUNITIES,
    DAY,
    OPPORTUNITY,
    accepted,
    decider,
    decision,
    repository,
    sheet_for,
    spec,
)  # fmt: skip
from tests.book3.test_decider import opportunity_record
from tests.packs.test_book_sheet import Alerts, Common, Sheet, body
from tests.packs.test_private_pack import plant

SC_A = COMMON_OPPORTUNITIES[0]["opportunity_id"]


def test_book3_s_sheet_is_registered_for_the_pack_step_and_only_packed_books_get_one(tmp_path):
    assert BOOK3_AI in SHEETS
    sheets = book_sheets((BOOK1_RULES, BOOK3_AI), tmp_path, cfg={})
    assert list(sheets) == [BOOK3_AI] and isinstance(sheets[BOOK3_AI], LazySheet)
    assert book_sheets((BOOK1_RULES,), tmp_path, cfg={}) == {}  # Book 3 not live: no sheet, nothing built


def test_the_sheet_lists_book3_s_built_trades_and_the_common_widths(tmp_path):
    sheet = sheet_for(repository(tmp_path, [spec()]))
    assert [(o["opportunity_id"], o["fired"], o["trade"]["width"]) for o in sheet["opportunities"]] == [
        (OPPORTUNITY, True, 100.0)
    ]
    assert sheet["common_widths"] == {SC_A: [300.0, 200.0, 100.0]}


def test_a_day_with_no_tradable_strategy_gives_an_empty_sheet(tmp_path):
    assert sheet_for(repository(tmp_path))["opportunities"] == []


def test_the_decider_reproduces_the_pack_step_s_sheet_and_a_pick_on_it_trades(tmp_path):
    root = repository(tmp_path, [spec()])
    run = decider(root).decide(accepted(root, decision([OPPORTUNITY]), sheet_for(root)))
    assert opportunity_record(run.run)["chosen_action"] == "trade"  # the sheet the session saw is the one D2 re-gives


def test_common_widths_skip_the_no_trade_entry_and_an_unreadable_version():
    common = CommonPack(DAY, {"opportunities": [*COMMON_OPPORTUNITIES, {"opportunity_id": "x", "strategy": "gone",
                                                                         "version": 9}]})  # fmt: skip
    assert common_widths(common, lambda name, version: (300, 200) if name == "sc-a" else None) == {SC_A: [300.0, 200.0]}
    assert common_widths(CommonPack(DAY, {}), lambda name, version: None) == {}


def test_a_sheet_that_cannot_be_built_refuses_that_book_alone_and_is_built_once(tmp_path):
    plant(tmp_path)
    calls, alerts = [], Alerts()

    def broken():
        calls.append(1)
        raise KeyError("risk_free_rate")

    good = Sheet()
    packs = WrittenPacks(Common(), PrivatePackBuilder(tmp_path), PackStore(tmp_path), time(15, 0),
                         (BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI), sheets={BOOK2_HYBRID: LazySheet(lambda: good),
                         BOOK3_AI: LazySheet(broken)}, alerts=alerts, isolated=(BOOK2_HYBRID, BOOK3_AI))  # fmt: skip
    packs.build(DAY)
    assert body(tmp_path, BOOK1_RULES) and body(tmp_path, BOOK2_HYBRID)["evaluation"]["rule_default"] == ["opp-1"]
    assert not PackStore(tmp_path).private_path(BOOK3_AI, DAY).exists()
    assert alerts.sent == [SHEET_REFUSED.format(day=DAY, book=BOOK3_AI, error="KeyError: 'risk_free_rate'")]
    lazy = LazySheet(lambda: calls.append(2) or good)
    lazy.sheet(BOOK2_HYBRID, DAY, Common().build(DAY, None))
    lazy.sheet(BOOK2_HYBRID, DAY, Common().build(DAY, None))
    assert calls == [1, 2]  # built on first use, then kept
