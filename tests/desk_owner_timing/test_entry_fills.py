"""E8 rules 1-9 and 12, acceptance 5, 6, 8 and 10: an entry handed over at 15:15 fills at the due mark after the card's
delivery time T plus R, all legs or none, or misses with one fixed reason; the record carries T, R, the due mark and the
copy's hash; a rerun after a stop finishes the same entry without checking funds against its own fills."""

from __future__ import annotations

import dataclasses
from datetime import date, timedelta

import pytest

from fno.books.account import PaperAccount
from fno.constants import (
    OUTCOME_NOT_OPENED,
    OUTCOME_OPENED,
    OUTCOME_PROTECTION_UNVERIFIED,
    OUTCOME_REFUSED,
    VIEW_VERDICT,
)
from fno.desk.owner_timing.availability import AlwaysAvailable
from fno.desk.owner_timing.clock import OwnerTimingClock
from fno.desk.owner_timing.due_fill import DueFill
from fno.desk.owner_timing.entry_fills import BLOCKED, DECIDED_AFTER_CARD, OwnerTimingEntries
from fno.desk.owner_timing.entry_range import ApprovedLimit
from fno.desk.owner_timing.outcomes import ENTRY, MISSED_FUNDS, MISSED_NO_CARD, MISSED_NO_QUOTE
from fno.desk.records import DeskEvent, DeskRecords
from fno.desk.snapshot import SnapshotError
from fno.desk.wiring import open_desk_journal
from tests.desk.builders import CHARGES, DAY, STRATEGY, fly_order, fly_rows
from tests.desk_owner_timing.fakes import CALENDAR, FixedRisk, Marks, MemoryTimingLog, Settable, ist

FILL_DAY = date(2026, 10, 15)
CARD = ist(DAY, 15, 16)
DUE = ist(FILL_DAY, 10, 15)


@pytest.fixture
def marks():
    return Marks()


@pytest.fixture
def parts(marks):
    clock = OwnerTimingClock(60, CALENDAR, AlwaysAvailable())
    risk, log, now = FixedRisk(), MemoryTimingLog(), Settable(ist(FILL_DAY, 10, 20))
    entries = OwnerTimingEntries(DueFill(clock, marks, ApprovedLimit(), CHARGES), risk, log, VIEW_VERDICT, 60, now)
    return entries, risk, log, now


def apply(root, entries, order=None, card=CARD):
    order = order or fly_order()
    with open_desk_journal(order.book, root) as journal:
        return entries.apply(order, card, journal)


def account(root, book="book1_rules"):
    return DeskRecords(PaperAccount(root, book))


def outcomes(root):
    return [(e["outcome"], e["reason"]) for e in account(root).event_rows("t1")]


def test_a_card_never_delivered_misses_without_a_mark(root, parts):
    entries, _, log, _ = parts
    assert apply(root, entries, card=None) == MISSED_NO_CARD
    assert outcomes(root) == [(OUTCOME_NOT_OPENED, MISSED_NO_CARD)] and not log.records


def test_a_decision_committed_after_the_card_misses(root, parts):
    entries, _, log, _ = parts
    assert apply(root, entries, card=ist(DAY, 15, 4)) == DECIDED_AFTER_CARD
    assert log.records[0].due_mark is None and outcomes(root) == [(OUTCOME_NOT_OPENED, DECIDED_AFTER_CARD)]


def test_nothing_happens_before_the_due_marks_window_closes(root, parts, marks):
    entries, _, log, now = parts
    marks.put(DUE, fly_rows())
    now.now = DUE + timedelta(seconds=60)
    assert apply(root, entries) is None
    assert not log.records and not account(root).event_rows()


def test_every_leg_fills_at_the_due_mark_with_its_record(root, parts, marks):
    entries, risk, log, _ = parts
    marks.put(DUE, fly_rows())
    reason = apply(root, entries)
    assert reason.startswith("4 legs filled at the 10:15 mark") and risk.asked == ["t1"]
    fills = account(root).fill_rows("t1")
    assert len(fills) == 4 and {f["snapshot_id"] for f in fills} == {"a16_20261015_1015"}
    record = log.records[0]
    assert (record.account, record.view, record.kind, record.reaction_minutes) == ("book1_rules", "verdict", ENTRY, 60)
    assert (record.order_time, record.due_mark, record.fill_mark, record.outcome) == (CARD, DUE, DUE, OUTCOME_OPENED)
    assert record.snapshot_id == "a16_20261015_1015" and len(record.snapshot_sha256) == 64
    assert outcomes(root) == [(OUTCOME_OPENED, reason)]
    assert account(root).event_rows("t1")[0]["day"] == FILL_DAY.isoformat()


def test_one_leg_without_a_quote_fills_nothing(root, parts, marks):
    entries, risk, log, _ = parts
    marks.put(DUE, fly_rows({(25200, "CE"): {"valid": False, "reason": "no trade today"}}))
    assert apply(root, entries) == MISSED_NO_QUOTE
    assert not account(root).fill_rows() and not risk.asked and log.records[0].fill_mark is None


def test_funds_short_at_the_fill_misses_with_the_priced_copy(root, parts, marks):
    entries, risk, log, _ = parts
    risk.miss_reason = MISSED_FUNDS
    marks.put(DUE, fly_rows())
    assert apply(root, entries) == MISSED_FUNDS
    assert not account(root).fill_rows() and log.records[0].snapshot_id == "a16_20261015_1015"


def test_an_open_trade_that_blocks_new_risk_refuses_the_entry(root, parts, marks):
    entries, _, _, now = parts
    marks.put(DUE, fly_rows())
    apply(root, entries)
    with open_desk_journal("book1_rules", root) as journal:
        journal.record_event(DeskEvent("t1:unverified", FILL_DAY, "book1_rules", STRATEGY, "t1", "d-t1", "", "",
                                       OUTCOME_PROTECTION_UNVERIFIED, "fixture"))  # fmt: skip
    later = ist(date(2026, 10, 16), 10, 15)
    marks.put(later, fly_rows())
    now.now = later + timedelta(minutes=5)
    second = dataclasses.replace(fly_order("t2"), decided_at=ist(FILL_DAY, 15, 5))
    reason = apply(root, entries, second, card=ist(FILL_DAY, 15, 16))
    assert account(root).event_rows("t2")[0]["outcome"] == OUTCOME_REFUSED
    assert reason == BLOCKED.format(trades=f"t1 ({OUTCOME_PROTECTION_UNVERIFIED})", book="book1_rules")
    assert not account(root).fill_rows("t2")


def test_a_rerun_after_a_stop_finishes_the_same_entry_without_re_checking_funds(root, parts, marks):
    entries, risk, log, _ = parts
    marks.put(DUE, fly_rows())
    order = fly_order()
    with open_desk_journal(order.book, root) as journal:  # a run that stopped after its fills
        priced = entries.due_fill.price(order, entries.due_fill.schedule(order, CARD))
        for quote in priced.quotes:
            journal.record_fill(priced.maker.record(quote, "open"))
    risk.miss_reason = MISSED_FUNDS  # its own fills would now count against it
    assert apply(root, entries).startswith("4 legs filled") and not risk.asked
    assert len(account(root).fill_rows("t1")) == 4


def test_a_rerun_whose_copy_no_longer_prices_fails_the_step(root, parts, marks):
    entries, _, _, _ = parts
    marks.put(DUE, fly_rows())
    order = fly_order()
    with open_desk_journal(order.book, root) as journal:
        priced = entries.due_fill.price(order, entries.due_fill.schedule(order, CARD))
        journal.record_fill(priced.maker.record(priced.quotes[0], "open"))
    marks.store.files.clear()
    with pytest.raises(SnapshotError):
        apply(root, entries)
