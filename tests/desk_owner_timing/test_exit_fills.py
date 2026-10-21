"""E8 rules 1-3, 7, 9 and 12: an alerted exit closes at the due mark after the alert's delivery time T plus R, short
legs first; a leg without a valid quote waits and fills at a later mark; a mark past the last expiry is left to E7."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from fno.books.account import PaperAccount
from fno.constants import OUTCOME_CLOSED, OUTCOME_PENDING_EXIT, VIEW_VERDICT
from fno.desk.owner_timing.availability import AlwaysAvailable
from fno.desk.owner_timing.clock import OwnerTimingClock
from fno.desk.owner_timing.exit_fills import OwnerTimingExits
from fno.desk.owner_timing.outcomes import EXIT
from fno.desk.records import DeskRecords
from fno.desk.status import open_positions
from fno.desk.wiring import open_desk_journal
from tests.desk.builders import CHARGES, DAY, EXPIRY, at, contract, enter, fly_order, fly_rows, write_snapshot
from tests.desk_owner_timing.fakes import CALENDAR, Marks, MemoryTimingLog, Settable, ist

BOOK = "book1_rules"
FILL_DAY = date(2026, 10, 15)
ALERT = ist(DAY, 15, 20)
DUE = ist(FILL_DAY, 10, 15)
NO_PROTECTION = {(25200, "CE"): {"valid": False, "reason": "no trade today"}}


@pytest.fixture
def opened(root, store, snapshots, entry_desk):
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))
    enter(root, snapshots, entry_desk, fly_order())


@pytest.fixture
def parts(exit_desk):
    marks, log, now = Marks(), MemoryTimingLog(), Settable(ist(FILL_DAY, 10, 20))
    clock = OwnerTimingClock(60, CALENDAR, AlwaysAvailable())
    return OwnerTimingExits(clock, marks, exit_desk, log, VIEW_VERDICT, 60, CHARGES, now), marks, log, now


def records(root):
    return DeskRecords(PaperAccount(root, BOOK))


def apply(root, exits, alert=ALERT):
    with open_desk_journal(BOOK, root) as journal:
        position = open_positions(journal.records)[0]
        return exits.apply(BOOK, position, alert, journal)


def outcomes(root):
    return [e["outcome"] for e in records(root).event_rows("t1")]


def test_the_exit_closes_every_leg_at_the_due_mark(root, opened, parts):
    exits, marks, log, _ = parts
    marks.put(DUE, fly_rows())
    assert apply(root, exits).startswith("every leg closed")
    assert not open_positions(records(root)) and outcomes(root)[-1] == OUTCOME_CLOSED
    record = log.records[0]
    assert (record.kind, record.order_time, record.due_mark, record.fill_mark) == (EXIT, ALERT, DUE, DUE)
    assert record.outcome == OUTCOME_CLOSED and record.snapshot_id == "a16_20261015_1015"


def test_nothing_happens_before_the_due_mark(root, opened, parts):
    exits, marks, log, now = parts
    marks.put(DUE, fly_rows())
    now.now = DUE + timedelta(seconds=30)
    assert apply(root, exits) is None and not log.records


def test_protection_without_a_quote_waits_and_fills_at_a_later_mark(root, opened, parts):
    exits, marks, log, now = parts
    marks.put(DUE, fly_rows(NO_PROTECTION))
    assert "retried at the next marks" in apply(root, exits)
    assert [h[0].contract for h in open_positions(records(root))[0].holdings] == [contract(25200, "CE")]
    assert outcomes(root)[-1] == OUTCOME_PENDING_EXIT and log.records[0].outcome == OUTCOME_PENDING_EXIT
    later = DUE + timedelta(minutes=15)
    marks.put(later, fly_rows())
    now.now = later + timedelta(minutes=5)
    assert apply(root, exits).startswith("every leg closed")
    assert not open_positions(records(root)) and log.records[-1].fill_mark == later


def test_a_rerun_skips_copies_older_than_the_last_closing_fill(root, opened, parts):
    exits, marks, log, now = parts
    marks.put(DUE, fly_rows({(25000, "CE"): {"valid": False, "reason": "no trade today"}}))
    marks.put(DUE + timedelta(minutes=15), fly_rows(NO_PROTECTION))
    now.now = DUE + timedelta(minutes=20)
    apply(root, exits)  # shorts close at 10:30; protection waits
    now.now = DUE + timedelta(minutes=50)
    assert "retried at the next marks" in apply(root, exits)  # the 10:15 copy is older than the 10:30 fills


def test_a_mark_after_the_last_expiry_is_left_to_settlement(root, opened, parts):
    exits, marks, _, now = parts
    expiry_day = ist(EXPIRY, 15, 20)
    now.now = expiry_day + timedelta(days=1, hours=-3)
    assert apply(root, exits, alert=expiry_day) is None
    assert marks.read == []


def test_no_copy_at_any_mark_leaves_the_exit_waiting_silently(root, opened, parts):
    exits, _, log, _ = parts
    assert apply(root, exits) is None and not log.records
