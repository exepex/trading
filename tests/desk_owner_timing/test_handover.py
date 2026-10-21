"""E8 rules 1, 10 and 11, judge 203 condition 2: from the live date the daily run hands entries over (`entry_pending`,
E4's own refusal unchanged except the complete-capture demand) and alerts an ordered exit, keeping the position open;
the alert's Slack server time is the exit's T. Before the live date, or with none set, E4 runs as before."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from fno.books.account import PaperAccount
from fno.cards.deliveries import DeliveryLog
from fno.constants import OUTCOME_ENTRY_PENDING, OUTCOME_EXIT_ORDERED, OUTCOME_OPENED, OUTCOME_REFUSED
from fno.desk.exit_rules import ExitRule
from fno.desk.exits import ExitDesk
from fno.desk.owner_timing.exit_alerts import AlertThenWait
from fno.desk.owner_timing.live_switch import LiveFromEntries, LiveFromExits
from fno.desk.owner_timing.order_record import KeptOrders, order_data
from fno.desk.owner_timing.order_times import DeliveredCards
from fno.desk.owner_timing.pending import pending_entries, pending_exits
from fno.desk.owner_timing.pending_entries import HANDED_OVER, PendingEntries
from fno.desk.records import DeskRecords
from fno.desk.status import open_positions
from fno.desk.wiring import open_desk_journal
from tests.desk.builders import CHARGES, DAY, at, enter, fly_order, fly_rows, passed, write_snapshot
from tests.desk_owner_timing.fakes import SLACK_TS, Due, MemoryTimingLog, Poster

BOOK = "book1_rules"


class Attempts(DeliveryLog):
    def __init__(self, *attempts: dict):
        self.rows = [(f"a{n}.json", a) for n, a in enumerate(attempts)]

    def write(self, day, metadata):
        raise NotImplementedError

    def attempts(self, day):
        return self.rows


@pytest.fixture
def execution(store):
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))


def records(root):
    return DeskRecords(PaperAccount(root, BOOK))


def test_a_handed_over_entry_waits_for_its_fill_and_fills_nothing(root, store, snapshots, entry_desk, execution):
    desk = LiveFromEntries(DAY, entry_desk, PendingEntries(60, KeptOrders(store, store)))
    result = enter(root, snapshots, desk, fly_order())
    assert (result.outcome, result.reason) == (OUTCOME_ENTRY_PENDING, HANDED_OVER.format(minutes=60))
    assert not records(root).fill_rows() and pending_entries(BOOK, records(root))[0].trade_id == "t1"
    assert enter(root, snapshots, desk, fly_order()).outcome == OUTCOME_ENTRY_PENDING  # a rerun repeats nothing
    assert len(records(root).event_rows("t1")) == 1
    assert store.get("book1_rules/orders/t1.json") == order_data(fly_order())  # the order as decided, kept first


def test_e4s_own_refusal_still_refuses_the_hand_over(root, store, snapshots, entry_desk, execution):
    late = fly_order(decided_at=at(15, 16))
    result = enter(root, snapshots, PendingEntries(60, KeptOrders(store, store)), late)
    assert result.outcome == OUTCOME_REFUSED and "not before the execution snapshot" in result.reason
    assert not pending_entries(BOOK, records(root)) and store.get("book1_rules/orders/t1.json") is None


def test_an_incomplete_execution_capture_still_hands_over(root, store, snapshots):
    write_snapshot(store, "partial", fly_rows(), at(15, 15), at(15, 15, 40), complete=False)
    assert (
        enter(root, snapshots, PendingEntries(60, KeptOrders(store, store)), fly_order(), "partial").outcome
        == OUTCOME_ENTRY_PENDING
    )


@pytest.mark.parametrize("live_from", [None, DAY + timedelta(days=1)], ids=["no date", "later date"])
def test_before_the_live_date_e4_fills_as_before(root, store, snapshots, entry_desk, execution, live_from):
    desk = LiveFromEntries(live_from, entry_desk, PendingEntries(60, KeptOrders(store, store)))
    assert enter(root, snapshots, desk, fly_order()).outcome == OUTCOME_OPENED


def review(root, snapshots, desk):
    snapshot = snapshots.snapshot(DAY, "later")
    with open_desk_journal(BOOK, root) as journal:
        return desk.review(BOOK, snapshot, journal, {"t1": [Due()]}, passed(snapshot))


@pytest.fixture
def ordered(root, store, snapshots, entry_desk, execution):
    enter(root, snapshots, entry_desk, fly_order())
    write_snapshot(store, "later", fly_rows(), at(15, 16), at(15, 16, 40))


def test_an_ordered_exit_is_alerted_once_and_the_position_stays_open(root, snapshots, alerts, settlements, clock,
                                                                      ordered):  # fmt: skip
    poster, log = Poster(), MemoryTimingLog()
    desk = ExitDesk(CHARGES, alerts, settlements, clock, LiveFromExits(DAY, AlertThenWait(poster, log)))
    [result] = review(root, snapshots, desk)
    assert result.outcome == OUTCOME_EXIT_ORDERED and len(poster.posted) == 1 and "EXIT trade t1" in poster.posted[0]
    assert "time stop" in poster.posted[0] and "Rs" not in poster.posted[0]  # never a price
    assert log.alert_time(BOOK, "t1") == datetime.fromtimestamp(float(SLACK_TS), UTC)
    assert pending_exits(records(root))[0].trade_id == "t1" and len(records(root).fill_rows("t1")) == 4
    review(root, snapshots, desk)
    assert len(poster.posted) == 1


def test_an_undelivered_exit_alert_is_sent_again_and_has_no_order_time(root, snapshots, alerts, settlements, clock,
                                                                        ordered):  # fmt: skip
    poster, log = Poster(ts=None), MemoryTimingLog()
    desk = ExitDesk(CHARGES, alerts, settlements, clock, AlertThenWait(poster, log))
    assert "NOT delivered" in review(root, snapshots, desk)[0].reason and log.alert_time(BOOK, "t1") is None
    poster.ts = SLACK_TS
    review(root, snapshots, desk)
    assert len(poster.posted) == 2 and log.alert_time(BOOK, "t1") is not None


def test_before_the_live_date_the_exit_closes_at_the_snapshot(root, snapshots, alerts, settlements, clock, ordered):
    poster = Poster()
    desk = ExitDesk(CHARGES, alerts, settlements, clock, LiveFromExits(None, AlertThenWait(poster, MemoryTimingLog())))
    review(root, snapshots, desk)
    assert not open_positions(records(root)) and not poster.posted


def test_the_cards_order_time_is_slacks_first_accepted_non_test_post():
    sent = {"slack": {"sent": True, "server_time_utc": "2026-10-14T09:46:00+00:00"}}
    cards = DeliveredCards(Attempts({"slack": {"sent": False}}, sent | {"test": True}, sent))
    assert cards.delivered(DAY) == datetime(2026, 10, 14, 9, 46, tzinfo=UTC)
    assert DeliveredCards(Attempts({"slack": {"sent": False}})).delivered(date(2026, 10, 14)) is None


class Priced(ExitRule):
    name = "fixture"

    def reached(self, position, context):
        return "net Rs 1,234.50: fixture"


def test_an_exit_alert_never_carries_a_figure(root, snapshots, alerts, settlements, clock, ordered):
    poster = Poster()
    desk = ExitDesk(CHARGES, alerts, settlements, clock, AlertThenWait(poster, MemoryTimingLog()))
    snapshot = snapshots.snapshot(DAY, "later")
    with open_desk_journal(BOOK, root) as journal:
        desk.review(BOOK, snapshot, journal, {"t1": [Priced()]}, passed(snapshot))
    assert "(exit ordered)" in poster.posted[0] and not any(c.isdigit() for c in poster.posted[0].split("trade t1")[1])
