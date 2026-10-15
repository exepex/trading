"""Composition root of story G8 (protocol v4 scoring): G7's forecast files, G7's series rules for outcomes, the frozen
threshold tools, the look records and the slot registrations. Swapping any of them is one class plus one line here."""

from __future__ import annotations

from ...config import ROOT
from .inputs import ForecastFiles
from .records import LookRecords, NoRegistrations
from .scoring import V4Scoring
from .thresholds import FrozenToolThresholds

FORECASTS_FOLDER = ROOT / "research" / "forecasts" / "v4"  # G7's files (agreed layout)
SCORES_FOLDER = ROOT / "research" / "forecasts" / "v4_scores"
FREEZE_FILE = ROOT / "research" / "forecasts" / "FREEZE_v4.md"


def build_scoring() -> V4Scoring:
    """Before the freeze no slot is registered (the ledger row the freeze writes names them)."""
    return V4Scoring(ForecastFiles(FORECASTS_FOLDER), _outcomes(), NoRegistrations())


def build_look_records() -> LookRecords:
    return LookRecords(SCORES_FOLDER, FREEZE_FILE)


def build_thresholds() -> FrozenToolThresholds:
    return FrozenToolThresholds(ROOT / "tools")


def _outcomes():
    raise NotImplementedError("G7's series.py adapter: added when G7's code lands (G8 builds against it)")
