"""The instructor's read adapters over recorded inputs (story MS-INS, part a): b's catalogue and snapshot source for
the captures, A6's events file for the scheduled events. Neither reads anything live."""

from collections.abc import Sequence
from datetime import date

from ...research_data.events import Event, in_window
from ..constants import RoadCode
from ..contracts.roads import RoadCatalogue
from ..contracts.snapshot import SlotSnapshot, SnapshotSource, SnapshotUnavailable


class RecordedSnapshotArchive:
    def __init__(self, catalogue: RoadCatalogue, source: SnapshotSource):
        self.catalogue, self.source = catalogue, source

    def snapshot(self, road: RoadCode, session: date) -> SlotSnapshot | None:
        day = next((d for d in self.catalogue.day(session) if d.road.code == road), None)
        if day is None or not day.status.open:
            return None
        try:
            return self.source.for_road(day)
        except SnapshotUnavailable:
            return None


class RecordedEventCalendar:
    def __init__(self, events: Sequence[Event]):
        self.events = list(events)

    def known_between(self, decided_on: date, after: date, through: date) -> tuple[date, ...]:
        return tuple(sorted({e.day for e in in_window(self.events, decided_on, after, through)}))
