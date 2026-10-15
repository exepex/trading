"""Story E2b criterion 3: the committed fill rows hold no touch, and the only way a filled leg's other quote side
follows from them is a buy and a sell of one contract at one snapshot. Within one account that happens only when an
entry is unwound (the stated exception); across accounts, two accounts trading one contract on opposite sides at the
same execution snapshot (the second stated exception, judge 118 addendum 1)."""

from datetime import timedelta

import pytest

from fno.books.account import PaperAccount
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, FILL_UNWIND, OPTION_CALL, OPTION_PUT, SIDE_BUY, SIDE_SELL
from fno.desk.exit_rules import TimeExit
from fno.desk.records import FILL_COLUMNS, DeskRecords
from tests.desk.builders import DAY, DECIDED_AT, contract, enter, fly_order, fly_rows
from tests.desk.test_exits import review, snapshot_on

CE, PE = OPTION_CALL, OPTION_PUT
NEXT = DAY + timedelta(days=1)
REACHED = {"t1": [TimeExit(days_before_expiry=13)]}  # 27 Oct - 13 days: reached on 14 Oct (test_exits)


@pytest.fixture
def opened(root, store, snapshots, entry_desk):
    from tests.desk.builders import write_snapshot
    from tests.desk.test_entries import at

    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))
    assert enter(root, snapshots, entry_desk, fly_order()).outcome == "opened"


def rows(root, *books):
    return [r for book in books or (BOOK1_RULES,) for r in DeskRecords(PaperAccount(root, book)).fill_rows()]


def both_sides(fills) -> set[tuple[str, str]]:
    """(snapshot, contract) pairs with a buy and a sell in the rows: there, bid and ask are both public."""
    sides: dict[tuple[str, str], set[str]] = {}
    for row in fills:
        sides.setdefault((row["snapshot_id"], row["contract"]), set()).add(row["side"])
    return {key for key, seen in sides.items() if seen == {SIDE_BUY, SIDE_SELL}}


def test_the_fill_rows_hold_no_touch():
    assert not {"quote_bid", "quote_ask", "bid", "ask", "bid_qty", "ask_qty"} & set(FILL_COLUMNS)


def test_an_opened_entry_and_its_close_at_a_later_snapshot_reveal_no_second_side(root, store, snapshots, exit_desk,
                                                                                 clock, opened):  # fmt: skip
    assert both_sides(rows(root)) == set()
    snapshot_on(store, clock, NEXT, "next", fly_rows())
    review(root, snapshots, exit_desk, NEXT, "next", REACHED)
    assert both_sides(rows(root)) == set() and len(rows(root)) == 8  # opened at "exec", closed at "next"


def test_a_pending_exit_reveals_no_second_side(root, store, snapshots, exit_desk, clock, opened):
    snapshot_on(store, clock, NEXT, "next", fly_rows({(25000, CE): None}))
    review(root, snapshots, exit_desk, NEXT, "next", REACHED)
    assert both_sides(rows(root)) == set()


def test_only_an_unwind_reveals_both_sides_within_one_account(root, store, snapshots, entry_desk):
    from tests.desk.builders import write_snapshot
    from tests.desk.test_entries import at

    write_snapshot(store, "exec", fly_rows({(25000, PE): {"valid": False}}), at(15, 15), at(15, 15, 40))
    enter(root, snapshots, entry_desk, fly_order())
    fills = rows(root)
    unwound = {("exec", r["contract"]) for r in fills if r["action"] == FILL_UNWIND}
    assert both_sides(fills) == unwound == {("exec", contract(25200, CE)), ("exec", contract(24800, PE)),
                                            ("exec", contract(25000, CE))}  # fmt: skip


def test_two_accounts_on_opposite_sides_of_one_contract_at_one_snapshot_reveal_both(
    root, store, snapshots, exit_desk, clock, entry_desk
):
    """The second exception: nothing in E4 stops two accounts from trading one contract on opposite sides at the same
    execution snapshot (each account is filled on its own); here book 1 closes at "next" while book 2 opens there."""
    from tests.desk.builders import write_snapshot
    from tests.desk.test_entries import at

    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))
    enter(root, snapshots, entry_desk, fly_order())
    snapshot_on(store, clock, NEXT, "next", fly_rows())
    review(root, snapshots, exit_desk, NEXT, "next", REACHED)
    order = fly_order(trade_id="t2", book=BOOK2_HYBRID, decided_at=DECIDED_AT + timedelta(days=1))
    second = enter(root, snapshots, entry_desk, order, snapshot_id="next", day=NEXT)
    assert second.outcome == "opened", second
    assert both_sides(rows(root)) == set() and both_sides(rows(root, BOOK2_HYBRID)) == set()
    assert both_sides(rows(root, BOOK1_RULES, BOOK2_HYBRID))  # together they reveal the touch of "next"


def test_an_exit_at_the_snapshot_that_opened_the_trade(root, store, snapshots, exit_desk, clock, opened):
    """Whether a time exit can close at the opening snapshot (which would reveal both sides) is pinned here."""
    clock.set(at_close())
    results = review(root, snapshots, exit_desk, DAY, "exec", REACHED)
    revealed = both_sides(rows(root))
    assert revealed == set(), f"an exit at the opening snapshot revealed {revealed}: {results}"


def at_close():
    from tests.desk.test_entries import at

    return at(15, 20)
