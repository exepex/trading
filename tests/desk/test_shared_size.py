"""Story E4d: a book's entries at one snapshot share its displayed size (criteria 1-7). Two short iron flies of
`builders.py` (65 units each) sell the same 25000 PE at the bid; the first that fits fills, a later one that no longer
fits is refused, never over-filled."""

import csv
import re

import pytest

from fno.books.account import PaperAccount
from fno.constants import (
    BOOK1_RULES,
    BOOK2_HYBRID,
    FILL_OPEN,
    FILL_UNWIND,
    OPTION_CALL,
    OPTION_PUT,
    OUTCOME_NOT_OPENED,
    OUTCOME_OPENED,
    SHORT_LEG_NOT_SELLABLE,
    SIDE_BUY,
    SIDE_SELL,
    SIZE_SHARED_IN_BOOK,
    STRUCTURE_CALL_CREDIT_SPREAD,
    STRUCTURE_LONG_CALL,
)
from fno.desk.entry_check import entry_problems, taken_units
from fno.desk.records import DeskRecords
from fno.research_engine.structures import BOUGHT, SOLD

from .builders import DAY, FLY_QUOTES, at, contract, enter, fly_order, fly_rows, write_snapshot
from .test_entry_check import str1_order

CE, PE = OPTION_CALL, OPTION_PUT
SHORT, WING = (25000, PE), (25200, CE)


def shared(strike_kind, units=65, taken=65):
    already = f"{taken} already taken in this book at this snapshot"
    return f"{SIZE_SHARED_IN_BOOK} ({contract(*strike_kind)}, {units} units, {already})"


def snapshot_with(store, snapshots, changes, extra=(), snapshot_id="exec"):
    write_snapshot(store, snapshot_id, fly_rows(changes) + list(extra), at(15, 15), at(15, 15, 40))
    return snapshots.snapshot(DAY, snapshot_id)


def two_flies(root, snapshots, entry_desk, second=None):
    first = enter(root, snapshots, entry_desk, fly_order("t1"))
    return first, enter(root, snapshots, entry_desk, second or fly_order("t2"))


def written(root, trade_id, book=BOOK1_RULES):
    account = PaperAccount(root, book)
    return DeskRecords(account).fill_rows(trade_id), [r for r in account.ledger_rows() if r.get("trade_id") == trade_id]


@pytest.mark.parametrize("bid_size, second_opens", [(100, False), (129, False), (130, True), (131, True)])
def test_two_entries_share_the_short_leg_s_bid_size(root, store, snapshots, entry_desk, bid_size, second_opens):
    """Criterion 1: 65 + 65 against 100 (the orchestrator's fixture) and the boundary at 129 / 130: the first opens; the
    second opens only if the size covers both, else it is refused by the check with nothing written for it."""
    snapshot_with(store, snapshots, {SHORT: {"bid_qty": bid_size}})
    first, second = two_flies(root, snapshots, entry_desk)
    assert first.outcome == OUTCOME_OPENED
    if second_opens:
        assert second.outcome == OUTCOME_OPENED
        return
    assert (second.outcome, second.reason, second.refused_by_check) == (OUTCOME_NOT_OPENED, shared(SHORT), True)
    assert written(root, "t2") == ([], [])


def test_the_same_two_entries_in_two_books_both_open(root, store, snapshots, entry_desk):
    """Criterion 2: never pooled across books; each paper account counts only its own records."""
    snapshot_with(store, snapshots, {SHORT: {"bid_qty": 100}})
    first, second = two_flies(root, snapshots, entry_desk, fly_order("t2", book=BOOK2_HYBRID))
    assert first.outcome == second.outcome == OUTCOME_OPENED
    assert len(written(root, "t2", BOOK2_HYBRID)[0]) == 4


def test_a_leg_failing_alone_records_its_e4c_code(root, store, snapshots, entry_desk):
    """Criterion 3: two lots (130 units) against 100 fail on their own: E4c's code, not `size_shared_in_book`."""
    snapshot_with(store, snapshots, {SHORT: {"bid_qty": 100}})
    _, second = two_flies(root, snapshots, entry_desk, fly_order("t2", lots=2))
    assert second.reason == f"{SHORT_LEG_NOT_SELLABLE} ({contract(*SHORT)}, 130 units)"


def test_a_rerun_returns_the_recorded_outcomes_and_fills_nothing_twice(root, store, snapshots, entry_desk):
    """Criterion 4: the first entry's units come from its recorded fill rows; a rerun repeats nothing."""
    snapshot_with(store, snapshots, {SHORT: {"bid_qty": 100}})
    before = two_flies(root, snapshots, entry_desk)
    rows = DeskRecords(PaperAccount(root, BOOK1_RULES)).fill_rows()
    again = two_flies(root, snapshots, entry_desk)
    assert [(r.outcome, r.reason) for r in again] == [(r.outcome, r.reason) for r in before]
    assert not any(r.refused_by_check for r in again)  # a replay is never a new refusal: no second alert
    assert DeskRecords(PaperAccount(root, BOOK1_RULES)).fill_rows() == rows


def test_a_rerun_after_a_crash_between_fills_and_event_does_not_refuse_itself(root, store, snapshots, entry_desk):
    """Criterion 4: the entry being checked never counts its own trade's rows."""
    snapshot_with(store, snapshots, {SHORT: {"bid_qty": 100}})
    enter(root, snapshots, entry_desk, fly_order("t1"))
    (events,) = root.rglob(f"{BOOK1_RULES}/**/desk_events.csv")
    events.write_text(events.read_text().splitlines()[0] + "\n")  # the crash: t1's fills kept, its event not written
    assert enter(root, snapshots, entry_desk, fly_order("t1")).outcome == OUTCOME_OPENED
    assert len(written(root, "t1")[0]) == 4  # E1's fills are idempotent by fill ID


def long_call(trade_id="t1"):
    return str1_order(STRUCTURE_LONG_CALL, 0, ((25200, CE, BOUGHT),), trade_id)


def selling_the_wing(trade_id="t2"):
    """A vertical that sells 25200 CE at the bid (and buys 25000 CE): the contract the long call holds as protection.
    The check reads only legs and sides, so the fly's own strikes serve."""
    return str1_order(STRUCTURE_CALL_CREDIT_SPREAD, 200, ((25200, CE, SOLD), (25000, CE, BOUGHT)), trade_id)


@pytest.mark.parametrize("bid_size, second_opens", [(129, False), (130, True)])
def test_a_held_protective_leg_counts_its_sell_back_need_on_the_bid(
    root, store, snapshots, entry_desk, bid_size, second_opens
):
    """Criterion 5: the long call bought 65 of 25200 CE (no sell row yet), so 65 of its bid is held for selling it back;
    a later entry selling 25200 CE short at the bid fits only if the bid size covers both."""
    snapshot_with(store, snapshots, {WING: {"bid_qty": bid_size}})
    first = enter(root, snapshots, entry_desk, long_call())
    second = enter(root, snapshots, entry_desk, selling_the_wing())
    assert first.outcome == OUTCOME_OPENED
    expected = (OUTCOME_OPENED, "") if second_opens else (OUTCOME_NOT_OPENED, shared(WING))
    assert (second.outcome, second.reason if not second_opens else "") == expected


def test_the_reason_and_its_event_row_hold_no_quote_figure(root, store, snapshots, entry_desk):
    """Criterion 6: the book's own units only, never a bid, ask or size of the snapshot."""
    snapshot_with(store, snapshots, {SHORT: {"bid_qty": 100}})
    two_flies(root, snapshots, entry_desk)
    (events,) = root.rglob(f"{BOOK1_RULES}/**/desk_events.csv")
    (row_t2,) = [r for r in csv.DictReader(events.open()) if r["trade_id"] == "t2"]
    assert row_t2["reason"] == shared(SHORT)
    figures = {float(v) for quote in FLY_QUOTES.values() for v in quote} | {100.0, 1000.0}
    text = " ".join(v for k, v in row_t2.items() if k != "snapshot_sha256").replace(contract(*SHORT), "")
    assert not {float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)} & figures


def test_no_units_taken_is_e4c_s_check(store, snapshots):
    """Criterion 7: with nothing taken (the default, and an empty map) the check is E4c's."""
    snapshot = snapshot_with(store, snapshots, {SHORT: {"bid_qty": 64}})
    legs = fly_order().legs()
    e4c = [f"{SHORT_LEG_NOT_SELLABLE} ({contract(*SHORT)}, 65 units)"]
    assert entry_problems(snapshot, legs, 65) == entry_problems(snapshot, legs, 65, {}) == e4c


def fill(trade_id, strike_kind, side, units, action=FILL_OPEN, opening="sold", snapshot_id="exec", sha=None):
    return {"trade_id": trade_id, "contract": contract(*strike_kind), "side": side, "units": str(units),
            "action": action, "opening_side": opening, "snapshot_id": snapshot_id, "snapshot_sha256": sha}  # fmt: skip


def test_taken_units_counts_every_fill_row_at_the_snapshot_by_its_side(store, snapshots):
    """Judge 201: every row at this snapshot by its side, an unwind's closing fills included; a protective leg's
    sell-back need is only what it still holds; other snapshots, other contents and the trade itself are left out."""
    snapshot = snapshot_with(store, snapshots, {})
    here = snapshot.sha256
    rows = [
        fill("a", SHORT, SIDE_SELL, 65, sha=here),
        fill("a", WING, SIDE_BUY, 65, opening="bought", sha=here),  # held: 65 to sell back
        fill("b", WING, SIDE_BUY, 65, opening="bought", sha=here),
        fill("b", WING, SIDE_SELL, 65, FILL_UNWIND, "bought", sha=here),  # sold back on the guard path: none held
        fill("b", SHORT, SIDE_BUY, 65, FILL_UNWIND, sha=here),  # an unwind buys back at the ask
        fill("me", SHORT, SIDE_SELL, 65, sha=here),
        fill("c", SHORT, SIDE_SELL, 65, snapshot_id="earlier", sha=here),
        fill("d", SHORT, SIDE_SELL, 65, sha="another day's snapshot of the same name"),
    ]
    assert taken_units(rows, snapshot, "me") == {
        (contract(*SHORT), SIDE_SELL): 65,
        (contract(*SHORT), SIDE_BUY): 65,
        (contract(*WING), SIDE_BUY): 130,
        (contract(*WING), SIDE_SELL): 65 + 65,  # b's sell-back row and a's held need
    }
