"""Composition root of story G8 (protocol v4 scoring): G7's forecast files, G7's series rules for outcomes, the frozen
threshold tools, the look records and the slot registrations. Swapping any of them is one class plus one line here."""

from __future__ import annotations

from datetime import date
from functools import cache

from ...config import ROOT
from ...forecast_v4.sessions import is_scored_session
from ...intraday.rv_table import RvTable
from .cutoff_moves import RecordedCutoffMoves
from .days import DayCounts, DayFiles, LateDaysOut, day_counts
from .drive_forecasts import CombinedForecasts, DriveForecastRecords, chosen_paths, verified_files
from .g7_series import G7Series
from .inputs import ForecastFiles
from .outcomes import SeriesOutcomes
from .primary import primary_values
from .reconcile import AiSlotDays, sessions_not_late
from .records import LookRecords, SlotRegistry
from .scoring import V4Scoring
from .slot_file import SlotFile
from .thresholds import FrozenToolThresholds

FORECASTS_FOLDER = ROOT / "research" / "forecasts" / "v4"  # G7's files (agreed layout)
SCORES_FOLDER = ROOT / "research" / "forecasts" / "v4_scores"
FREEZE_FILE = ROOT / "research" / "forecasts" / "FREEZE_v4.md"
SLOTS_FILE = ROOT / "research" / "forecasts" / "v4_slots.csv"  # the slot registrations (response 287)
CLOSES_FILE = ROOT / "research" / "data" / "nifty-panel" / "warmup_closes.csv"  # O6
INTRADAY_FOLDER = ROOT / "research" / "data" / "intraday"  # A16's live rv/ files (never A16b's rv-candle/)
V4_DAYS_FOLDER = ROOT / "research" / "data" / "v4_days"  # G10: one label file per live day, written by the capture


def build_scoring() -> V4Scoring:
    """The slots registered in `v4_slots.csv` (none before the freeze commit writes them). A system_late day is
    out of the forecasts and the outcomes for every forecaster (G10)."""
    inputs = LateDaysOut(_forecasts(), _outcomes(), DayFiles(V4_DAYS_FOLDER))
    return V4Scoring(inputs, inputs, _registry())


def build_ai_slot_days() -> AiSlotDays:
    from ...storage.wiring import build_session_calendar

    calendar = build_session_calendar()
    sessions = sessions_not_late(lambda d: is_scored_session(calendar, d), DayFiles(V4_DAYS_FOLDER))
    return AiSlotDays(ForecastFiles(FORECASTS_FOLDER), _registry(), sessions)


def build_day_counts(as_of: date) -> DayCounts:
    flags = RecordedCutoffMoves(RvTable(INTRADAY_FOLDER).rows())  # A16's 15:30 run commits each day's flag
    return day_counts(DayFiles(V4_DAYS_FOLDER).labels(), flags.moved, as_of)


def build_look_records() -> LookRecords:
    return LookRecords(SCORES_FOLDER, FREEZE_FILE)


def build_thresholds() -> FrozenToolThresholds:
    return FrozenToolThresholds(ROOT / "tools")


@cache
def _forecasts() -> CombinedForecasts:
    """G7's repository CSVs and the records kept in Drive (G7b completion, part e), built once per command. With no
    receipt under the records folder the Drive source is left out, so such a report needs no Drive access."""
    from ...forecast_v4_rules.drive_records import RECORDS_FOLDER
    from ...forecast_v4_rules.wiring import IMPLIED_METHOD_FILES, method_sha256
    from ...storage.data_wiring import DATA_AREA, build_drive_cache, receipt_folder

    receipts = receipt_folder().under(f"{DATA_AREA}/{RECORDS_FOLDER}")
    sources = [ForecastFiles(FORECASTS_FOLDER)]
    if receipts:
        method = method_sha256(IMPLIED_METHOD_FILES)
        paths = chosen_paths([r.path.removeprefix(f"{DATA_AREA}/") for r in receipts], method)
        sources.append(DriveForecastRecords(verified_files(build_drive_cache(), DATA_AREA, paths), method))
    return CombinedForecasts(sources)


def _outcomes() -> SeriesOutcomes:
    rv = RvTable(INTRADAY_FOLDER)
    return SeriesOutcomes(G7Series(CLOSES_FILE.read_text(encoding="utf-8"), rv.rows))


def _registry() -> SlotRegistry:
    """One registry for scoring and the look's reconciliation: the committed slot registrations (none before the
    freeze commit writes the first rows)."""
    return SlotFile(SLOTS_FILE, _first_eligible, _frozen_on)


def _frozen_on() -> date | None:
    records = build_look_records()
    return records.frozen_on() if records.frozen() else None


def _first_eligible(question: str) -> date | None:
    """The first live session after the freeze with a value of the question's primary baseline (None before the
    freeze, or while there is none)."""
    records = build_look_records()
    if not records.frozen():
        return None
    after = records.frozen_on()
    values = primary_values(question, _forecasts())
    return min((d for d, v in values.items() if v.live and v.value is not None and d > after), default=None)
