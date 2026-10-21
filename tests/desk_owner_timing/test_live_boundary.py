"""Response 228 point 6 (ChatGPT review 128): the live boundary and late recovery. A decision made before the live date
is filled once by E4 and never queued; one made on the live date is handed over and filled once by E8; an E4 exit still
waiting on the live date is alerted and finished once by E8, never closing a leg twice. A prior-day order recovered
sessions later keeps its card's T and its own due mark, filled or missed there, never at a later mark."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from fno.books.account import PaperAccount
from fno.constants import OUTCOME_ENTRY_PENDING, OUTCOME_OPENED, VIEW_VERDICT
from fno.desk.exits import ExitDesk
from fno.desk.owner_timing.availability import AlwaysAvailable
from fno.desk.owner_timing.clock import OwnerTimingClock
from fno.desk.owner_timing.due_fill import DueFill
from fno.desk.owner_timing.entry_fills import OwnerTimingEntries
from fno.desk.owner_timing.entry_range import ApprovedLimit
from fno.desk.owner_timing.exit_alerts import AlertThenWait
from fno.desk.owner_timing.exit_fills import OwnerTimingExits
from fno.desk.owner_timing.live_switch import LiveFromEntries, LiveFromExits
from fno.desk.owner_timing.order_record import KeptOrders
from fno.desk.owner_timing.outcomes import MISSED_NO_QUOTE
from fno.desk.owner_timing.pending import pending_entries, pending_exits
from fno.desk.owner_timing.pending_entries import PendingEntries
from fno.desk.records import DeskRecords
from fno.desk.status import open_positions
from fno.desk.wiring import open_desk_journal
from tests.desk.builders import CHARGES, DAY, at, contract, enter, fly_order, fly_rows, passed, write_snapshot
from tests.desk_owner_timing.fakes import CALENDAR, Due, FixedRisk, Marks, MemoryTimingLog, Poster, Settable, ist

BOOK = "book1_rules"
THU, FRI = date(2026, 10, 15), date(2026, 10, 16)
CARD = ist(DAY, 15, 16)
DUE = ist(THU, 10, 15)
NO_PROTECTION = {(25200, "CE"): {"valid": False, "reason": "no trade today"}}


def records(root):
    return DeskRecords(PaperAccount(root, BOOK))


def owner_entries(marks, now):
    clock = OwnerTimingClock(60, CALENDAR, AlwaysAvailable())
    log = MemoryTimingLog()
    return OwnerTimingEntries(DueFill(clock, marks, ApprovedLimit(), CHARGES), FixedRisk(), log, VIEW_VERDICT, 60,
                              now), log  # fmt: skip


def fill_waiting(root, store, entries) -> list[str]:
    """What the step does for each waiting entry: its kept order, applied against the account."""
    reasons = []
    for pending in pending_entries(BOOK, records(root)):
        with open_desk_journal(BOOK, root) as journal:
            reasons.append(entries.apply(KeptOrders(store, store).order(pending), CARD, journal))
    return reasons


@pytest.fixture
def execution(store):
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))


@pytest.mark.parametrize(("live_from", "queued"), [(THU, False), (DAY, True)], ids=["day before", "on the live date"])
def test_each_entry_is_filled_exactly_once_on_its_own_side_of_the_live_date(root, store, snapshots, entry_desk,
                                                                            execution, live_from, queued):  # fmt: skip
    desk = LiveFromEntries(live_from, entry_desk, PendingEntries(60, KeptOrders(store, store)))
    outcome = enter(root, snapshots, desk, fly_order()).outcome
    assert outcome == (OUTCOME_ENTRY_PENDING if queued else OUTCOME_OPENED)
    assert bool(pending_entries(BOOK, records(root))) is queued
    marks = Marks()
    marks.put(DUE, fly_rows())
    entries, _ = owner_entries(marks, Settable(DUE + timedelta(minutes=5)))
    fill_waiting(root, store, entries)
    fill_waiting(root, store, entries)  # a rerun finds nothing left to fill
    fills = records(root).fill_rows("t1")
    assert len(fills) == 4 and {f["snapshot_id"] for f in fills} == {"a16_20261015_1015" if queued else "exec"}


def test_an_e4_exit_waiting_across_the_live_date_is_alerted_and_finished_once(root, store, snapshots, entry_desk,
                                                                              alerts, settlements, clock):  # fmt: skip
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))
    enter(root, snapshots, entry_desk, fly_order())
    poster, log = Poster(), MemoryTimingLog()
    desk = ExitDesk(CHARGES, alerts, settlements, clock, LiveFromExits(THU, AlertThenWait(poster, log)))

    def review(day, name):
        snapshot = snapshots.snapshot(day, name)
        with open_desk_journal(BOOK, root) as journal:
            desk.review(BOOK, snapshot, journal, {"t1": [Due()]}, passed(snapshot))

    write_snapshot(store, "before", fly_rows(NO_PROTECTION), at(15, 16), at(15, 16, 40))
    review(DAY, "before")  # E4 closes what it can; the protection waits
    held = [leg.contract for leg, _ in open_positions(records(root))[0].holdings]
    assert held == [contract(25200, "CE")] and not poster.posted
    clock.set(at(15, 20, day=THU))
    write_snapshot(store, "live", fly_rows(NO_PROTECTION), at(15, 16, day=THU), at(15, 16, 40, day=THU), day=THU)
    review(THU, "live")  # the live date: alerted once, nothing closed at the snapshot
    review(THU, "live")
    assert len(poster.posted) == 1 and pending_exits(records(root))[0].trade_id == "t1"
    marks, mark = Marks(), ist(FRI, 10, 15)
    marks.put(mark, fly_rows())
    owner_clock, now = OwnerTimingClock(60, CALENDAR, AlwaysAvailable()), Settable(mark + timedelta(minutes=5))
    closer = ExitDesk(CHARGES, alerts, settlements, clock)
    exits = OwnerTimingExits(owner_clock, marks, closer, log, VIEW_VERDICT, 60, CHARGES, now)
    with open_desk_journal(BOOK, root) as journal:
        exits.apply(BOOK, pending_exits(journal.records)[0], log.alert_time(BOOK, "t1"), journal)
    closes = [f["contract"] for f in records(root).fill_rows("t1")][4:]
    assert sorted(closes) == sorted(leg.contract for leg in fly_order().legs())  # every leg closed exactly once
    assert not open_positions(records(root))


@pytest.mark.parametrize("first_copy", [True, False], ids=["filled at its own mark", "missed at its own mark"])
def test_a_prior_day_order_recovered_two_sessions_later_keeps_its_t_and_due_mark(root, first_copy):
    marks = Marks()
    if first_copy:
        marks.put(DUE, fly_rows())
    marks.put(ist(FRI, 10, 15), fly_rows())  # a later copy is never used for this order
    entries, log = owner_entries(marks, Settable(ist(FRI, 10, 20)))
    with open_desk_journal(BOOK, root) as journal:
        reason = entries.apply(fly_order(), CARD, journal)
    record = log.records[0]
    assert (record.order_time, record.due_mark) == (CARD, DUE)
    if first_copy:
        assert (record.fill_mark, record.snapshot_id, record.outcome) == (DUE, "a16_20261015_1015", OUTCOME_OPENED)
    else:
        assert reason == MISSED_NO_QUOTE and not records(root).fill_rows()
        assert (record.fill_mark, record.snapshot_id) == (None, "")
    assert marks.read == [DUE]  # FRI's copy is never read for it
