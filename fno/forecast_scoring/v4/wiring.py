"""Composition root of story G8 (protocol v4 scoring): G7's forecast files, G7's series rules for outcomes, the frozen
threshold tools, the look records, the slot registrations and (G10 completion, criterion 6) the day labels: the release
records read from Drive through O9's verified cache plus the one rule for a day without a record. Swapping any of them
is one class plus one line here."""

from __future__ import annotations

from datetime import date

from ...config import ROOT
from ...forecast_v4.sessions import is_scored_session
from ...intraday.rv_table import RvTable
from ...v4_pack.paths import DAYS_FOLDER, DEADLINES_FOLDER
from .cutoff_moves import RecordedCutoffMoves
from .days import DayCounts, LateDaysOut, LiveDayLabels, day_counts
from .deadlines import DeadlineVerdicts, LateCommitmentsOut, unchecked_days
from .g7_series import G7Series
from .inputs import ForecastFiles
from .outcomes import SeriesOutcomes
from .primary import primary_values
from .reconcile import AiSlotDays, sessions_not_late
from .records import LookRecords, SlotRegistry
from .release_days import ReleasedDays
from .scoring import V4Scoring
from .slot_file import SlotFile
from .thresholds import FrozenToolThresholds

FORECASTS_FOLDER = ROOT / "research" / "forecasts" / "v4"  # G7's files (agreed layout)
SCORES_FOLDER = ROOT / "research" / "forecasts" / "v4_scores"
FREEZE_FILE = ROOT / "research" / "forecasts" / "FREEZE_v4.md"
SLOTS_FILE = ROOT / "research" / "forecasts" / "v4_slots.csv"  # the slot registrations (response 287)
CLOSES_FILE = ROOT / "research" / "data" / "nifty-panel" / "warmup_closes.csv"  # O6
INTRADAY_FOLDER = ROOT / "research" / "data" / "intraday"  # A16's live rv/ files (never A16b's rv-candle/)


def build_scoring() -> V4Scoring:
    """The slots registered in `v4_slots.csv` (none before the freeze commit writes them). A system_late day is
    out of the forecasts and the outcomes for every forecaster (G10)."""
    inputs = LateDaysOut(_checked_forecasts(), _outcomes(), build_day_labels(_today()))
    return V4Scoring(inputs, inputs, build_slot_registry())


def build_ai_slot_days() -> AiSlotDays:
    sessions = sessions_not_late(_is_session(), build_day_labels(_today()))
    return AiSlotDays(ForecastFiles(FORECASTS_FOLDER), build_slot_registry(), sessions)


def build_day_counts(as_of: date) -> DayCounts:
    flags = RecordedCutoffMoves(RvTable(INTRADAY_FOLDER).rows())  # A16's 15:30 run commits each day's flag
    labels = build_day_labels(as_of)
    unchecked = [day for day in build_unchecked_days() if day <= as_of]
    return day_counts(labels.labels(), flags.moved, as_of, labels.pending(), len(unchecked))


def build_unchecked_days() -> list[date]:
    """The live days with a row whose 15:10 deadline has no verdict yet (a recorded look refuses while one exists)."""
    from ...constants import V4_DAY_SYSTEM_LATE
    from .scoring import QUESTIONS

    late = {d for d, label in build_day_labels(_today()).labels().items() if label.label == V4_DAY_SYSTEM_LATE}
    return [day for day in unchecked_days(_checked_forecasts(), QUESTIONS) if day not in late]  # out for everyone


def _checked_forecasts() -> LateCommitmentsOut:
    """G7's and M1's files with the 15:10 verdicts applied: a late live row is no forecast that day."""
    return LateCommitmentsOut(ForecastFiles(FORECASTS_FOLDER), DeadlineVerdicts(_drive_records(DEADLINES_FOLDER)))


def _drive_records(folder: str):
    from ...storage.data_wiring import DATA_AREA, build_drive_cache, receipt_folder
    from .drive_records import DriveRecords

    return DriveRecords(receipt_folder(), build_drive_cache, DATA_AREA, folder)


def build_day_labels(today: date) -> LiveDayLabels:
    """The one day source of the three readers above: Drive's release records, and `missing_label` for the rest."""
    from ...config import load_config
    from ...daily.wiring import live_dates
    from ...v4_pack.sessions import sessions_between

    records = ReleasedDays(_drive_records(DAYS_FOLDER))
    return LiveDayLabels(records, sessions_between(_is_session()), live_dates(load_config())["forecasts_v4"], today)


def _is_session():
    from ...storage.wiring import build_session_calendar

    calendar = build_session_calendar()
    return lambda d: is_scored_session(calendar, d)


def _today() -> date:
    from ...models import now_ist

    return now_ist().date()


def build_look_records() -> LookRecords:
    return LookRecords(SCORES_FOLDER, FREEZE_FILE)


def build_thresholds() -> FrozenToolThresholds:
    return FrozenToolThresholds(ROOT / "tools")


def _outcomes() -> SeriesOutcomes:
    rv = RvTable(INTRADAY_FOLDER)
    return SeriesOutcomes(G7Series(CLOSES_FILE.read_text(encoding="utf-8"), rv.rows))


def build_slot_registry() -> SlotRegistry:
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
    values = primary_values(question, ForecastFiles(FORECASTS_FOLDER))
    return min((d for d, v in values.items() if v.live and v.value is not None and d > after), default=None)
