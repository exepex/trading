"""Composition root of `fno/school/instructor/` (story MS-INS): the path reader over c's dashcam, b's recorded
captures, d's settlement source and A7's calendar (part a); the classifier over A6's events, e's frozen cards, d's
fill port for the hold-to-expiry value, G13's rate and the frozen rules card (part c). Part e adds the store."""

import hashlib
from pathlib import Path

from ...config import load_app_config
from ...research_data.events import read_events
from ...storage.wiring import EVENTS_FILE
from ..dashcam.wiring import build_dashcam
from ..drivers.cards import CARDS_FOLDER, load_cards
from ..execution.wiring import build_fill_port, build_settlement_source
from ..roads.wiring import build_road_services
from .adapters import CardStops, IstClock, NotYetReplayable, RecordedEventCalendar, RecordedSnapshotArchive
from .causes.classify import Classifier
from .causes.evidence import EvidenceBuilder
from .reader import PathReader

ROOT = Path(__file__).resolve().parents[3]
RULES_CARD = ROOT / "research" / "school" / "INSTRUCTOR_V1.md"


def rules_sha256() -> str:
    return hashlib.sha256(RULES_CARD.read_bytes()).hexdigest()


def build_path_reader() -> PathReader:
    roads = build_road_services()
    archive = RecordedSnapshotArchive(roads.catalogue, roads.snapshots)
    return PathReader(build_dashcam(), archive, build_settlement_source(), roads.calendar, IstClock())


def build_event_calendar() -> RecordedEventCalendar:
    return RecordedEventCalendar(read_events(EVENTS_FILE.read_text(encoding="utf-8")))


def build_classifier(config: dict | None = None) -> Classifier:
    cfg = config if config is not None else load_app_config()
    roads = build_road_services()
    archive = RecordedSnapshotArchive(roads.catalogue, roads.snapshots)
    stops = CardStops(load_cards(ROOT / CARDS_FOLDER).values())
    evidence = EvidenceBuilder(archive, build_event_calendar(), stops, NotYetReplayable(), build_fill_port(cfg),
                               float(cfg["risk_free_rate"]))  # fmt: skip
    return Classifier(evidence, rules_sha256())
