"""Story E4, exits: pending exits on missing quotes (criterion 3), protection_unverified (criterion 4), exit rules
closing at the next valid quotes (criterion 5), shorts first and protection last, settlement and point in time."""

from datetime import date, timedelta

import pytest

from fno.books.account import PaperAccount
from fno.books.equity import trade_positions
from fno.constants import (
    BOOK1_RULES,
    BOOK2_HYBRID,
    FILL_CLOSE,
    OPTION_CALL,
    OPTION_PUT,
    OUTCOME_CLOSED,
    OUTCOME_EXIT_ORDERED,
    OUTCOME_OPENED,
    OUTCOME_PENDING_EXIT,
    OUTCOME_PROTECTION_UNVERIFIED,
    OUTCOME_REFUSED,
    OUTCOME_SETTLEMENT_NEEDED,
    SIDE_BUY,
    SIDE_SELL,
)
from fno.costs import order_charges
from fno.desk.execution import PROTECTION_HELD
from fno.desk.exit_rules import ProfitTarget, StopLoss, TimeExit
from fno.desk.exits import HELD, NO_RULES
from fno.desk.records import DeskRecords
from fno.desk.snapshot import SnapshotError
from fno.desk.wiring import open_desk_journal

from .builders import CHARGES, DAY, LOT, at, contract, enter, fly_order, fly_rows, passed, write_snapshot

CE, PE = OPTION_CALL, OPTION_PUT
NEXT = DAY + timedelta(days=1)
LATER = DAY + timedelta(days=2)
HOLD = {"t1": [StopLoss(1e9)]}  # a rule that never fires


def review(root, snapshots, desk, day, snapshot_id, rules, book=BOOK1_RULES):
    snapshot = snapshots.snapshot(day, snapshot_id)
    with open_desk_journal(book, root) as journal:
        return desk.review(book, snapshot, journal, rules, passed(snapshot))


def snapshot_on(store, clock, day, snapshot_id, rows):
    write_snapshot(store, snapshot_id, rows, at(15, 15, day=day), at(15, 15, 40, day=day), day=day)
    clock.set(at(15, 20, day=day))


@pytest.fixture
def opened(root, store, snapshots, entry_desk):
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))
    assert enter(root, snapshots, entry_desk, fly_order()).outcome == OUTCOME_OPENED


def close_rows(root):
    rows = DeskRecords(PaperAccount(root, BOOK1_RULES)).fill_rows()
    return [(r["contract"], r["side"], float(r["price"]), r["snapshot_id"]) for r in rows if r["action"] == FILL_CLOSE]


def is_open(root):
    return trade_positions(PaperAccount(root, BOOK1_RULES).fills())["t1"].is_open


def outcomes(root, book=BOOK1_RULES):
    return [e["outcome"] for e in DeskRecords(PaperAccount(root, book)).event_rows("t1")]


def test_missing_exit_quotes_give_a_pending_exit_and_an_alert_never_a_stale_price(root, store, snapshots, exit_desk,
                                                                                  clock, alerts, opened):  # fmt: skip
    snapshot_on(store, clock, NEXT, "next", fly_rows({(25000, CE): None}))  # one short leg unquoted
    rules = {"t1": [TimeExit(days_before_expiry=13)]}  # 27 Oct - 13 days = 14 Oct: reached
    [result] = review(root, snapshots, exit_desk, NEXT, "next", rules)
    assert result.outcome == OUTCOME_PENDING_EXIT and "no quote in the snapshot" in result.reason
    assert PROTECTION_HELD in result.reason and len(alerts.sent) == 1 and OUTCOME_PENDING_EXIT in alerts.sent[0]
    assert close_rows(root) == [(contract(25000, PE), SIDE_BUY, 141.5, "next")]  # the quoted short only; no protection
    assert is_open(root)
    snapshot_on(store, clock, LATER, "later", fly_rows())  # the next scheduled snapshot: valid quotes
    [result] = review(root, snapshots, exit_desk, LATER, "later", {})
    assert result.outcome == OUTCOME_CLOSED and not is_open(root)
    assert close_rows(root)[1:] == [(contract(25000, CE), SIDE_BUY, 151.0, "later"),
                                    (contract(24800, PE), SIDE_SELL, 60.0, "later"),
                                    (contract(25200, CE), SIDE_SELL, 70.0, "later")]  # fmt: skip
    assert outcomes(root) == [OUTCOME_OPENED, OUTCOME_EXIT_ORDERED, OUTCOME_PENDING_EXIT, OUTCOME_CLOSED]


def test_unquotable_protection_marks_the_position_blocks_new_risk_and_exits_at_the_next_valid_quotes(
    root, store, snapshots, entry_desk, exit_desk, clock, alerts, opened
):
    snapshot_on(store, clock, NEXT, "next", fly_rows({(25200, CE): {"valid": False, "reason": "no size"}}))
    [result] = review(root, snapshots, exit_desk, NEXT, "next", HOLD)
    assert result.outcome == OUTCOME_PENDING_EXIT and len(result.alerts) == 2  # unverified, then pending
    assert outcomes(root) == [OUTCOME_OPENED, OUTCOME_PROTECTION_UNVERIFIED, OUTCOME_EXIT_ORDERED, OUTCOME_PENDING_EXIT]
    assert [c for c, *_ in close_rows(root)] == [contract(25000, CE), contract(25000, PE), contract(24800, PE)]
    assert is_open(root)  # not closed while an exit fill is missing
    refused = enter(root, snapshots, entry_desk, fly_order("t2", decided_at=at(15, 5, day=NEXT)), "next", NEXT)
    assert refused.outcome == OUTCOME_REFUSED
    assert "open trade t1 (protection_unverified) blocks new risk" in refused.reason
    other = enter(root, snapshots, entry_desk, fly_order("t2", book=BOOK2_HYBRID, decided_at=at(15, 5, day=NEXT)),
                  "next", NEXT)  # fmt: skip
    assert other.reason.startswith(contract(25200, CE))  # another book is not blocked: only the bad quote stops it
    snapshot_on(store, clock, LATER, "later", fly_rows())
    [result] = review(root, snapshots, exit_desk, LATER, "later", HOLD)
    assert result.outcome == OUTCOME_CLOSED and not is_open(root)
    allowed = enter(root, snapshots, entry_desk, fly_order("t3", decided_at=at(15, 5, day=LATER)), "later", LATER)
    assert allowed.outcome == OUTCOME_OPENED  # resolved: the book may open new risk again


def _net_if_closed(prices: dict) -> float:
    """Hand computation: opening premium and charges, then closing every leg at these (bid, ask) quotes."""
    opening = (150.0 + 140.0 - 71.0 - 60.5) * LOT - sum(
        order_charges(p, LOT, s, CHARGES)
        for p, s in [(71.0, SIDE_BUY), (60.5, SIDE_BUY), (150.0, SIDE_SELL), (140.0, SIDE_SELL)]  # fmt: skip
    )
    buys = [prices[(25000, CE)][1], prices[(25000, PE)][1]]
    sells = [prices[(25200, CE)][0], prices[(24800, PE)][0]]
    closing = (
        (sum(sells) - sum(buys)) * LOT
        - sum(order_charges(p, LOT, SIDE_BUY, CHARGES) for p in buys)
        - sum(order_charges(p, LOT, SIDE_SELL, CHARGES) for p in sells)
    )
    return opening + closing


CALM = {(25000, CE): (100.0, 101.0), (25000, PE): (95.0, 96.0), (25200, CE): (30.0, 31.0), (24800, PE): (25.0, 26.0)}
RALLY = {(25000, CE): (260.0, 262.0), (25000, PE): (40.0, 41.0), (25200, CE): (130.0, 132.0), (24800, PE): (5.0, 6.0)}


@pytest.mark.parametrize("prices, rule, fires", [
    (CALM, ProfitTarget, True), (CALM, StopLoss, False), (RALLY, StopLoss, True), (RALLY, ProfitTarget, False),
])  # fmt: skip
def test_an_exit_rule_reached_closes_the_trade_at_the_next_valid_quotes(root, store, snapshots, exit_desk, clock,
                                                                        opened, prices, rule, fires):  # fmt: skip
    rows = fly_rows({key: {"bid": bid, "ask": ask} for key, (bid, ask) in prices.items()})
    snapshot_on(store, clock, NEXT, "next", rows)
    net = _net_if_closed(prices)
    threshold = abs(net) - 0.01  # the rule fires exactly when its side is crossed
    [result] = review(root, snapshots, exit_desk, NEXT, "next", {"t1": [rule(threshold)]})
    if not fires:
        assert (result.outcome, close_rows(root)) == (HELD, []) and is_open(root)
        return
    assert result.outcome == OUTCOME_CLOSED and result.reason == f"every leg closed; net Rs {net:,.2f}"
    assert outcomes(root)[1] == OUTCOME_EXIT_ORDERED and not is_open(root)
    assert PaperAccount(root, BOOK1_RULES).closed_trades()[0].trade_id == "t1"


def test_price_rules_are_not_judged_at_the_snapshot_that_opened_the_position(root, snapshots, exit_desk, opened):
    [result] = review(root, snapshots, exit_desk, DAY, "exec", {"t1": [StopLoss(0.0)]})  # the spread alone is a loss
    assert result.outcome == HELD and close_rows(root) == []


def test_an_open_trade_without_exit_rules_is_alerted_and_held(root, store, snapshots, exit_desk, clock, alerts, opened):
    snapshot_on(store, clock, NEXT, "next", fly_rows())
    [result] = review(root, snapshots, exit_desk, NEXT, "next", {})
    assert (result.outcome, result.reason) == (HELD, NO_RULES) and NO_RULES in alerts.sent[0]


def test_a_leg_that_expired_before_its_exit_needs_settlement_and_is_never_priced(root, store, snapshots, exit_desk,
                                                                                 clock, alerts, opened):  # fmt: skip
    after = date(2026, 10, 28)
    snapshot_on(store, clock, after, "after", fly_rows())
    for _ in range(2):  # a rerun records and alerts once
        [result] = review(root, snapshots, exit_desk, after, "after", HOLD)
        assert result.outcome == OUTCOME_SETTLEMENT_NEEDED and "final settlement price" in result.reason
    assert close_rows(root) == [] and len(alerts.sent) == 1 and is_open(root)


def test_an_unsettled_expired_trade_blocks_the_book_s_new_risk(root, store, snapshots, entry_desk, exit_desk, clock,
                                                               opened):  # fmt: skip
    after = date(2026, 10, 28)
    snapshot_on(store, clock, after, "after", fly_rows())
    review(root, snapshots, exit_desk, after, "after", HOLD)
    refused = enter(root, snapshots, entry_desk, fly_order("t2", decided_at=at(15, 5, day=after)), "after", after)
    assert refused.outcome == OUTCOME_REFUSED  # judge 68: its stale mark must not let the book keep trading
    assert "open trade t1 (settlement_needed) blocks new risk in book1_rules" in refused.reason


def test_a_snapshot_older_than_the_last_fill_or_later_than_the_clock_is_refused(root, store, snapshots, exit_desk,
                                                                              clock, opened):  # fmt: skip
    write_snapshot(store, "early", fly_rows(), at(15, 0), at(15, 0, 30))
    with pytest.raises(SnapshotError, match="before"):
        review(root, snapshots, exit_desk, DAY, "early", {"t1": [TimeExit(0)]})
    write_snapshot(store, "next", fly_rows(), at(15, 15, day=NEXT), at(15, 15, 40, day=NEXT), day=NEXT)
    with pytest.raises(SnapshotError, match="after the run's time"):  # the clock is still on 14 Oct
        review(root, snapshots, exit_desk, NEXT, "next", {"t1": [TimeExit(0)]})
    assert close_rows(root) == []


def test_a_rerun_of_the_exit_review_repeats_nothing(root, store, snapshots, exit_desk, clock, alerts, opened):
    snapshot_on(store, clock, NEXT, "next", fly_rows({(25000, CE): None}))
    rules = {"t1": [TimeExit(13)]}
    first = review(root, snapshots, exit_desk, NEXT, "next", rules)
    ledger = PaperAccount(root, BOOK1_RULES).ledger_rows()
    second = review(root, snapshots, exit_desk, NEXT, "next", rules)
    assert [r.outcome for r in second] == [r.outcome for r in first] == [OUTCOME_PENDING_EXIT]
    assert PaperAccount(root, BOOK1_RULES).ledger_rows() == ledger and len(alerts.sent) == 1
