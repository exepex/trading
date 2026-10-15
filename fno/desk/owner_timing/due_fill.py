"""An order's owner-timing fill in two steps (story E8 rules 2-9): `schedule` gives its due mark when it is sent (or
why it misses), and `price` reads that mark's snapshot once the mark has passed. Every leg is priced before any fill
(E4c's rule): one leg without a valid quote misses the whole entry ("missed, no quote"); E4c's entry check and E4d's
shared size then run at the mark's own copy and miss it with their own code; an entry outside the owner's entry rule
is "missed, price moved". A miss is never retried at another mark or price."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime

from ..entries import EntryOrder
from ..entry_check import entry_problems, taken_units
from ..execution import FillMaker
from ..pricing import LegQuote, price_leg
from .clock import FillClock
from .entry_range import EntryRange
from .mark_levels import MarkSnapshot
from .mark_snapshots import MarkSnapshots
from .outcomes import ENTRY, MISSED_EXPIRED, MISSED_NO_QUOTE, MISSED_PRICE_MOVED, DueMark, Missed


@dataclass(frozen=True)
class PricedEntry:
    """Every leg of an entry priced at its due mark, inside the owner's entry rule: what the fill-day checks read."""

    due: DueMark
    mark: MarkSnapshot
    maker: FillMaker
    quotes: list[LegQuote]


class DueFill:
    def __init__(
        self, clock: FillClock, snapshots: MarkSnapshots, entry_range: EntryRange, charges: Mapping[str, float]
    ):
        self.clock, self.snapshots, self.entry_range = clock, snapshots, entry_range
        self.charges = dict(charges)

    def schedule(self, order: EntryOrder, sent_at: datetime) -> DueMark | Missed:
        due = self.clock.due(sent_at, ENTRY)
        if isinstance(due, DueMark) and due.session > order.expiry:
            return Missed(MISSED_EXPIRED)  # the contract stopped trading before the owner could act
        return due

    def price(
        self, order: EntryOrder, due: DueMark, book_fills: Iterable[Mapping[str, str]] = ()
    ) -> PricedEntry | Missed:
        """`book_fills`: the book's fill rows, so entries due at one mark share its displayed size (E4d)."""
        mark = self.snapshots.at(due.session, due.mark)
        if mark is None:
            return Missed(MISSED_NO_QUOTE)
        snapshot, units, trade_id = mark.prices, order.proposal.units, order.proposal.trade_id
        quotes = [price_leg(snapshot, leg, leg.side(opening=True), units) for leg in order.legs()]
        if not all(quote.fills for quote in quotes):
            return Missed(MISSED_NO_QUOTE, snapshot)
        problems = entry_problems(snapshot, order.legs(), units, taken_units(book_fills, snapshot, trade_id))
        if problems:  # E4c and E4d at the mark's own copy: protection sellable back, the book's shared size
            return Missed(problems[0], snapshot)
        maker = FillMaker(
            order.book, order.strategy, order.decision_id, order.proposal.trade_id, snapshot, self.charges
        )
        if not self.entry_range.admits(order, maker, quotes):
            return Missed(MISSED_PRICE_MOVED, snapshot)
        return PricedEntry(due, mark, maker, quotes)
