"""E8 rules 5-7 and 9, acceptance 5, 6 and 8: every leg priced at the due mark before any fill, the owner's price cap,
"missed, no quote" and "missed, contract expired"."""

from __future__ import annotations

import dataclasses
from datetime import date, datetime, timedelta

from fno.constants import FILL_OPEN
from fno.desk.owner_timing.availability import AlwaysAvailable
from fno.desk.owner_timing.clock import OwnerTimingClock
from fno.desk.owner_timing.due_fill import DueFill
from fno.desk.owner_timing.entry_range import ApprovedLimit
from fno.desk.owner_timing.mark_levels import MarkSnapshot
from fno.desk.owner_timing.mark_snapshots import MarkSnapshots
from fno.desk.owner_timing.outcomes import MISSED_EXPIRED, MISSED_NO_QUOTE, MISSED_PRICE_MOVED, DueMark, Missed
from fno.desk.snapshot import RecordedExecutionSnapshots
from tests.desk.builders import CHARGES, DictStore, fly_order, fly_rows, write_snapshot
from tests.desk_owner_timing.fakes import CALENDAR, ist

DECIDED, FILL_DAY = date(2026, 10, 14), date(2026, 10, 15)
DUE = DueMark(FILL_DAY, ist(FILL_DAY, 10, 15))


class OneMark(MarkSnapshots):
    def __init__(self, rows=None):
        self.store = DictStore()
        if rows is not None:
            started = DUE.mark
            write_snapshot(self.store, "a16", rows, started, started + timedelta(seconds=50), day=FILL_DAY)

    def at(self, day: date, mark: datetime):
        if (day, mark) != (DUE.session, DUE.mark) or not self.store.files:
            return None
        return MarkSnapshot(RecordedExecutionSnapshots(self.store).snapshot(day, "a16"), 25000.0)


def due_fill(rows=None) -> DueFill:
    clock = OwnerTimingClock(60, CALENDAR, AlwaysAvailable())
    return DueFill(clock, OneMark(rows), ApprovedLimit(), CHARGES)


def test_a_card_is_scheduled_for_the_next_mornings_mark():
    assert due_fill().schedule(fly_order(), ist(DECIDED, 15, 16)) == DUE


def test_an_entry_due_after_its_expiry_misses():
    order = dataclasses.replace(fly_order(), expiry=DECIDED)
    assert due_fill().schedule(order, ist(DECIDED, 15, 16)) == Missed(MISSED_EXPIRED)


def test_every_leg_quoted_inside_the_cap_fills():
    priced = due_fill(fly_rows()).price(fly_order(), DUE)
    assert len(priced.quotes) == 4 and priced.maker.snapshot.snapshot_id == "a16"


def test_one_leg_without_a_valid_quote_misses_the_whole_entry():
    rows = fly_rows({(25200, "CE"): {"valid": False, "reason": "no trade today"}})
    assert due_fill(rows).price(fly_order(), DUE) == Missed(MISSED_NO_QUOTE)


def test_no_snapshot_at_the_mark_misses():
    assert due_fill().price(fly_order(), DUE) == Missed(MISSED_NO_QUOTE)


def test_one_paisa_worse_than_the_approved_entry_misses():
    priced = due_fill(fly_rows()).price(fly_order(), DUE)
    at_touch = sum(priced.maker.fill(q, FILL_OPEN).amount for q in priced.quotes)
    assert not isinstance(due_fill(fly_rows()).price(fly_order(limit=at_touch), DUE), Missed)
    assert due_fill(fly_rows()).price(fly_order(limit=at_touch + 0.01), DUE) == Missed(MISSED_PRICE_MOVED)
