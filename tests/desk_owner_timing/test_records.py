"""E8 rules 11 and 12, judge 203 early view 1: E8's own records are write-once files per account (a shadow version in
its own folder), and a handed-over entry fills the order kept at its hand-over, never one rebuilt the next day."""

from __future__ import annotations

from datetime import date

import pytest

from fno.constants import BOOK1_RULES
from fno.desk.owner_timing import outcomes
from fno.desk.owner_timing.order_record import KeptOrders
from fno.desk.owner_timing.outcomes import ENTRY
from fno.desk.owner_timing.pending import OrderMissing, PendingEntry
from fno.desk.owner_timing.timing_log import StoreTimingLog, TimingRecord
from fno.storage.raw_store import LocalFolderStore, RawFileConflict
from tests.desk.builders import DAY, DictStore, fly_order
from tests.desk_owner_timing.fakes import ist

DUE = ist(date(2026, 10, 15), 10, 15)


def record(account=BOOK1_RULES, reason="filled") -> TimingRecord:
    return TimingRecord(account, "verdict", "t1", ENTRY, 60, ist(DAY, 15, 16), DUE, DUE, "a16", "ab" * 32, "opened",
                        reason)  # fmt: skip


def test_records_and_alerts_are_kept_once_per_account_and_mark(tmp_path):
    store = LocalFolderStore(tmp_path)  # write-once, as Drive's own store
    log = StoreTimingLog(store, store)
    log.record(record())
    log.record(record("shadow:b1-v2"))
    log.alerted(BOOK1_RULES, "t1", ist(DAY, 15, 40))
    written = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*.json")}
    assert written == {
        "book1_rules/fills/t1-entry-20261015T1015.json", "shadow/b1-v2/fills/t1-entry-20261015T1015.json",
        "book1_rules/alerts/t1.json",
    }  # fmt: skip
    assert log.alert_time(BOOK1_RULES, "t1") == ist(DAY, 15, 40) and log.alert_time("book2_hybrid", "t1") is None
    log.record(record())  # a rerun writes the same bytes
    with pytest.raises(RawFileConflict):
        log.record(record(reason="something else"))


def test_the_kept_order_is_exactly_the_decided_one():
    store = DictStore()
    orders = KeptOrders(store, store)
    order = fly_order("t2")
    orders.keep(order)
    orders.keep(order)  # a rerun keeps the same bytes
    assert list(store.files) == ["book1_rules/orders/t2.json"]
    kept = orders.order(PendingEntry(BOOK1_RULES, "t2", DAY))
    assert kept == order and kept.risk.entry_cash_rs == order.risk.entry_cash_rs


def test_an_entry_without_a_kept_order_is_refused():
    with pytest.raises(OrderMissing):
        KeptOrders(DictStore(), DictStore()).order(PendingEntry(BOOK1_RULES, "t1", DAY))


def test_every_fixed_miss_reason_is_in_the_one_table():
    reasons = {
        value for name, value in vars(outcomes).items() if name.startswith("MISSED_") and name != "MISSED_REASONS"
    }
    assert set(outcomes.MISSED_REASONS) == reasons | {outcomes.DECIDED_AFTER_CARD} and len(outcomes.MISSED_REASONS) == 9
