"""From E8's live date on (`config.yaml` `daily.live_from.owner_timing_fills`), the daily run hands entries to the
owner-timing fill and only alerts ordered exits; before it, E4 fills and closes at the execution snapshot as today.
The date is read from each snapshot's day, so a rerun of an earlier day keeps that day's rule. No date set: never."""

from __future__ import annotations

from datetime import date

from ..entries import EntryFiller, EntryOrder, EntryResult
from ..exit_timing import ExitTiming, ImmediateExits
from ..exits import ExitResult


def live(live_from: date | None, day: date) -> bool:
    return live_from is not None and day >= live_from


class LiveFromEntries(EntryFiller):
    def __init__(self, live_from: date | None, before: EntryFiller, after: EntryFiller):
        self.live_from, self.before, self.after = live_from, before, after

    def enter(self, order: EntryOrder, snapshot, journal, checks) -> EntryResult:
        chosen = self.after if live(self.live_from, snapshot.day) else self.before
        return chosen.enter(order, snapshot, journal, checks)


class LiveFromExits(ExitTiming):
    def __init__(self, live_from: date | None, after: ExitTiming):
        self.live_from, self.after, self.before = live_from, after, ImmediateExits()

    def defer(self, book, position, snapshot, journal) -> ExitResult | None:
        chosen = self.after if live(self.live_from, snapshot.day) else self.before
        return chosen.defer(book, position, snapshot, journal)
