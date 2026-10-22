"""The real roads and quality classes over planted captures, for the quality tests (story MS-P1b)."""

from dataclasses import dataclass

from fno.school.constants import RoadCode
from fno.school.contracts.roads import RoadDay
from fno.school.quality.gate import RoadQualityGate
from fno.school.roads.capture import CaptureReader
from fno.school.roads.catalogue import RecordedRoadCatalogue
from fno.school.roads.snapshots import RecordedSnapshotSource
from tests.school.roads.capture_builder import (
    CALENDAR,
    SESSION,
    DictStore,
    FixedExpiries,
    FixedLots,
    FixtureListing,
    Plant,
    road,
)

BANK = RoadCode.BANKNIFTY_MONTHLY


@dataclass
class Stack:
    store: DictStore
    catalogue: RecordedRoadCatalogue
    snapshots: RecordedSnapshotSource

    def road_day(self, code: RoadCode = BANK, session=SESSION) -> RoadDay:
        return next(d for d in self.catalogue.day(session) if d.road.code is code)


def stack(*plants: Plant) -> Stack:
    store = DictStore()
    for plant in plants:
        plant.write(store)
    reader = CaptureReader({dataset: store for dataset in {road(code).dataset for code in RoadCode}})
    return Stack(
        store, RecordedRoadCatalogue(CALENDAR, reader, FixedExpiries(), FixedLots()), RecordedSnapshotSource(reader)
    )


def good(**faults) -> Stack:
    return stack(Plant(road(BANK), **faults))


GATE = RoadQualityGate(FixtureListing())
