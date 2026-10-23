"""Composition root of the practice run (story MS-SIM-d1 to d4): the real archive, the real recorded captures for the
spreads, the pilot's configuration and calendar, handed to the runner as `PracticeParts`. Wiring only.

What it reads, all read-only: NSE's archived F&O and index-close files from the stores (no NSE request, d1), the
recorded 15:00 captures through MS-P1b's `CaptureReader` (the hash-checked Drive quote stores), the pilot's
configuration and the NSE session calendar. It writes nothing: the runner writes under the practice home."""

from datetime import date
from pathlib import Path

from ....composition import build_session_calendar
from ....config import ROOT
from ....quotes.recorder import DATASET
from ....quotes.weekly import WEEKLY_DATASET
from ....storage.quote_wiring import build_drive_only_quote_store
from ...contracts.roads import ROADS
from ...roads.capture import CaptureReader
from ...settings import school_settings
from ..history import edge1
from ..spreads.learner import SpreadLearner
from ..spreads.model import SpreadModel
from ..spreads.recorded import Skipped, recorded_snapshots
from ..terms import DatedTerms
from ..windows import PracticeWindows
from .fleet import PracticeParts
from .stores import build_history_chain, build_stored_library

FACTOR_FILE = ROOT / "research" / "data" / "margins" / "stress_factor.csv"
FIRST_CAPTURE = date(2026, 10, 13)  # the first forward capture: the spreads are learned from here


def learn_spreads(calendar, today: date, quotes_folder: Path) -> tuple[SpreadModel, Skipped]:
    """The spread model from every recorded capture since the first, each verified by the reader."""
    reader = CaptureReader(
        {dataset: build_drive_only_quote_store(quotes_folder, dataset=dataset) for dataset in (DATASET, WEEKLY_DATASET)}
    )
    skipped = Skipped()
    sessions = calendar.sessions(FIRST_CAPTURE, today)
    return SpreadLearner().learn(recorded_snapshots(reader, ROADS, sessions, skipped)), skipped


def build_practice_parts(
    cfg: dict, today: date, quotes_folder: Path, root: Path = ROOT
) -> tuple[PracticeParts, Skipped]:
    calendar = build_session_calendar()
    terms = DatedTerms(edge1.circular_lot_or_none, edge1.dated_charges(cfg["charges"]))
    spreads, skipped = learn_spreads(calendar, today, quotes_folder)
    chain = build_history_chain(build_stored_library())
    windows = PracticeWindows(school_settings(cfg).first_counted)
    return PracticeParts(cfg, root, FACTOR_FILE, calendar, chain, terms, windows, spreads), skipped
