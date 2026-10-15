"""Composition root of story G8 (protocol v4 scoring): G7's forecast files, G7's series rules for outcomes, the frozen
threshold tools, the look records and the slot registrations. Swapping any of them is one class plus one line here."""

from __future__ import annotations

from datetime import date

from ...config import ROOT
from ...intraday.rv_table import RvTable
from .audits import OpenAuditFile
from .cutoff_moves import RecordedCutoffMoves
from .days import DayCounts, DayFiles, LateDaysOut, day_counts
from .g7_series import G7Series
from .inputs import ForecastFiles
from .outcomes import SeriesOutcomes
from .records import LookRecords, NoRegistrations
from .scoring import V4Scoring
from .thresholds import FrozenToolThresholds

FORECASTS_FOLDER = ROOT / "research" / "forecasts" / "v4"  # G7's files (agreed layout)
SCORES_FOLDER = ROOT / "research" / "forecasts" / "v4_scores"
FREEZE_FILE = ROOT / "research" / "forecasts" / "FREEZE_v4.md"
CLOSES_FILE = ROOT / "research" / "data" / "nifty-panel" / "warmup_closes.csv"  # O6
INTRADAY_FOLDER = ROOT / "research" / "data" / "intraday"  # A16's live rv/ files (never A16b's rv-candle/)
OPEN_AUDITS_FILE = ROOT / "research" / "forecasts" / "v4_audits" / "open_audits.csv"  # G11 keeps it
V4_DAYS_FOLDER = ROOT / "research" / "data" / "v4_days"  # G10: one label file per live day, written by the capture


def build_scoring() -> V4Scoring:
    """Before the freeze no slot is registered (the ledger row the freeze writes names them). A system_late day is
    out of the forecasts and the outcomes for every forecaster (G10)."""
    inputs = LateDaysOut(ForecastFiles(FORECASTS_FOLDER), _outcomes(), DayFiles(V4_DAYS_FOLDER))
    return V4Scoring(inputs, inputs, NoRegistrations())


def build_day_counts(as_of: date) -> DayCounts:
    flags = RecordedCutoffMoves(RvTable(INTRADAY_FOLDER).rows())  # A16's 15:30 run commits each day's flag
    return day_counts(DayFiles(V4_DAYS_FOLDER).labels(), flags.moved, as_of)


def build_open_audits() -> OpenAuditFile:
    return OpenAuditFile(OPEN_AUDITS_FILE)


def build_look_records() -> LookRecords:
    return LookRecords(SCORES_FOLDER, FREEZE_FILE)


def build_thresholds() -> FrozenToolThresholds:
    return FrozenToolThresholds(ROOT / "tools")


def _outcomes() -> SeriesOutcomes:
    rv = RvTable(INTRADAY_FOLDER)
    return SeriesOutcomes(G7Series(CLOSES_FILE.read_text(encoding="utf-8"), rv.rows))
