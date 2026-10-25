"""Story E3, fills by book (orchestrator, 25 Oct 2026): the daily run's `fills` result is keyed by book, so Book 1 and
an AI book taking the same opportunity (the same trade ID) both keep their line; an old flat log (Book 1 only, before
the change) reads the same through the one reader; nothing recorded is rewritten."""

from fno.constants import BOOK1_RULES, BOOK2_HYBRID
from fno.desk.fill_results import book_refusals, trade_entries, trade_fills

OPENED = {"outcome": "opened", "reason": "4 legs filled", "snapshot_id": "exec_1", "sha256": "a" * 64}
REFUSED = {"outcome": "not filled", "reason": "blocked: the last session's exits were not reviewed"}
SAME = "2026-10-16-sc-a-v1:2026-11-23"


def test_two_books_on_one_trade_id_both_keep_their_line():
    result = {BOOK1_RULES: {"trades": {SAME: OPENED}}, BOOK2_HYBRID: {"trades": {SAME: {**OPENED, "sha256": "b" * 64}}}}
    assert [(book, trade) for book, trade, _ in trade_entries(result)] == [(BOOK1_RULES, SAME), (BOOK2_HYBRID, SAME)]
    assert trade_fills(result, BOOK2_HYBRID)[SAME]["sha256"] == "b" * 64
    assert trade_fills(result, BOOK1_RULES)[SAME] == OPENED


def test_an_old_flat_book1_log_reads_the_same_as_its_new_shape():
    old = {"t1": OPENED, BOOK2_HYBRID: REFUSED}  # before the change: trade IDs beside the books' own refusals
    new = {BOOK1_RULES: {"trades": {"t1": OPENED}}, BOOK2_HYBRID: REFUSED}
    assert trade_fills(old) == trade_fills(new) == {"t1": OPENED}
    assert trade_fills(old, BOOK1_RULES) == {"t1": OPENED}  # an old trade has no book: every book's view keeps it
    assert book_refusals(old) == book_refusals(new) == {BOOK2_HYBRID: REFUSED}


def test_step_level_fields_and_an_empty_result_are_no_trades():
    assert trade_fills({"status": "refused", "reason": "needs snapshot", "retry": False}) == {}
    assert trade_fills({}) == {} and book_refusals({}) == {}
