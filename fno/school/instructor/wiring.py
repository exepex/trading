"""Composition root of `fno/school/instructor/` (story MS-INS): the path reader over c's dashcam, b's recorded
captures and d's settlement source, and A6's events. Part a wires the readers; parts c and e add the card replay and
the instructor's own store."""

from ...research_data.events import read_events
from ...storage.wiring import EVENTS_FILE
from ..dashcam.wiring import build_dashcam
from ..execution.wiring import build_settlement_source
from ..roads.wiring import build_road_services
from .adapters import IstClock, RecordedEventCalendar, RecordedSnapshotArchive
from .reader import PathReader


def build_path_reader() -> PathReader:
    roads = build_road_services()
    archive = RecordedSnapshotArchive(roads.catalogue, roads.snapshots)
    return PathReader(build_dashcam(), archive, build_settlement_source(), roads.calendar, IstClock())


def build_event_calendar() -> RecordedEventCalendar:
    return RecordedEventCalendar(read_events(EVENTS_FILE.read_text(encoding="utf-8")))
