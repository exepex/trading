"""Composition root of the fetch-then-trigger pipeline (story O6): the only place that picks the concrete trigger,
Drive store, batch finder and alert sender, and which routine each download job fires. A new job is one line in JOBS;
a new routine is one line in ROUTINES (its two repository secrets); another store or trigger is one new class here."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import date, timedelta
from functools import cache

from ..composition import build_alert_sender
from ..constants import (
    DERIVED_AREA,
    ENV_ROUTINE_DRY_RUN_TOKEN,
    ENV_ROUTINE_DRY_RUN_TRIGGER_ID,
    PANEL_FORMAT_LEGACY,
    PANEL_FORMAT_UDIFF,
    PANEL_INDEX_CLOSE,
    PIPELINE_AREA,
    ROUTINE_DRY_RUN,
)
from ..models import now_ist
from ..research_data.nifty_panel import DailyFiles, NiftyPanelBuilder
from ..research_data.panel_append import PanelAppender
from ..storage import wiring as storage
from ..storage.raw_source import (
    NseArchiveSource,
    NseDailyFoSource,
    NseIndexCloseSource,
    NseLegacyFoSource,
    ParticipantOiSource,
)
from ..storage.raw_store import AreaStore, RawFileStore
from ..storage.revisions import RevisionIndex
from .batches import ManifestBatches
from .dispatcher import BatchDispatcher
from .dry_run import DryRunRoutine
from .index_closes import IndexCloseAppender
from .panel_days import PanelDayJob
from .records import PipelineRecords
from .run import PipelineRun
from .run_summary import RunSummaryStore
from .trigger import RoutineFireTrigger, RoutineTrigger, UnconfiguredTrigger

ROUTINES = {ROUTINE_DRY_RUN: (ENV_ROUTINE_DRY_RUN_TRIGGER_ID, ENV_ROUTINE_DRY_RUN_TOKEN)}  # name -> its two secrets
JOBS: dict[str, tuple[str, type[NseArchiveSource]]] = {
    "participant-oi-release": (ROUTINE_DRY_RUN, ParticipantOiSource),  # A8's daily check, then A9's upload
    "participant-oi-sweep": (ROUTINE_DRY_RUN, ParticipantOiSource),  # A8's monthly sweep: republished files (A11)
}  # job -> (routine it fires, dataset it downloads)
POINTER_DATASETS = frozenset(source.dataset for _, source in JOBS.values())  # what a routine accepts in a pointer
DRIVE_SETTINGS_MISSING = f"set {', '.join(storage.OWNER_UPLOAD_SETTINGS)} to use the pipeline's Drive areas"


def build_trigger(routine: str, env=os.environ) -> RoutineTrigger:
    """The routine's `/fire` trigger from its two secrets, or one that fails loudly naming the missing ones."""
    names = ROUTINES[routine]
    trigger_id, token = (env.get(name) for name in names)
    if not (trigger_id and token):
        return UnconfiguredTrigger(routine, tuple(n for n in names if not env.get(n)))
    return RoutineFireTrigger(routine, trigger_id, token)


def _project_drive(env=os.environ) -> RawFileStore:
    drive = storage.build_owner_drive(env)
    if drive is None:
        raise RuntimeError(DRIVE_SETTINGS_MISSING)
    return drive


def build_pipeline_run(job: str, days: int, env=os.environ) -> PipelineRun:
    """A job's batches of the last `days` days, fired to its routine, summarised in Drive's pipeline area."""
    routine, source = JOBS[job]
    since = now_ist().date() - timedelta(days=days)
    finder = ManifestBatches(
        source,
        storage.build_manifest_folder(),
        storage.build_revision_index(),
        since,
        (storage.RAW_AREA, storage.REVISIONS_AREA),
    )
    pipeline = AreaStore(_project_drive(env), PIPELINE_AREA)
    dispatcher = BatchDispatcher(PipelineRecords(pipeline, now_ist), build_trigger(routine, env))
    return PipelineRun(job, finder, dispatcher, RunSummaryStore(pipeline), build_alert_sender(), now_ist)


def build_dry_run_routine(env=os.environ) -> DryRunRoutine:
    """The example routine: reads the whole project folder, writes only the derived and pipeline areas."""
    drive = _project_drive(env)
    records = PipelineRecords(AreaStore(drive, PIPELINE_AREA), now_ist)
    return DryRunRoutine(drive, AreaStore(drive, DERIVED_AREA), records, ROUTINE_DRY_RUN)


def build_index_close_appender(env=os.environ) -> IndexCloseAppender:
    """The daily index-close job: NSE's index-close files as archived in the owner's Drive (never fetched here, so a
    row is the first archived version), appended to the panel folder's warm-up closes."""
    files = _drive_files(PANEL_INDEX_CLOSE, NseIndexCloseSource, AreaStore(_project_drive(env), storage.RAW_AREA))
    return IndexCloseAppender(files, storage.build_session_calendar(), storage.PANEL_FOLDER, build_alert_sender())


def _drive_files(label: str, source: type[NseArchiveSource], store: RawFileStore) -> DailyFiles:
    """A dataset's daily files as held in Drive (never fetched from NSE here)."""
    get = cache(lambda path: store.get(path))  # the input check and the builder read the same file once
    return DailyFiles(
        label, source.dataset, source.first_day, source.last_day,
        lambda day: (source.filename_for(day), get(source.path_for(day))),
    )  # fmt: skip


PROTOCOL_V3 = "research/forecasts/PROTOCOL_v3.md"  # G1 v3: the panel extends daily (responses 68-69); not frozen yet
FREEZE_V3 = "research/forecasts/FREEZE_v3.md"
VERSIONED_SOURCES = {"fo": NseDailyFoSource, "index-close": NseIndexCloseSource}


def require_v3_frozen() -> None:
    from ..config import ROOT
    from ..forecast.freeze_v2 import require_version_frozen
    from ..research_engine.ledger import Git

    require_version_frozen(ROOT, Git(ROOT).head(), PROTOCOL_V3, FREEZE_V3)


def first_archived_inputs(drive: RawFileStore) -> tuple[list[DailyFiles], DailyFiles]:
    """A3's inputs as first archived in Drive's raw area (A11 keeps later versions apart; they are never read here)."""
    raw = AreaStore(drive, storage.RAW_AREA)
    fo_files = [
        _drive_files(PANEL_FORMAT_UDIFF, NseDailyFoSource, raw),
        _drive_files(PANEL_FORMAT_LEGACY, NseLegacyFoSource, raw),
    ]
    return fo_files, _drive_files(PANEL_INDEX_CLOSE, NseIndexCloseSource, raw)


def later_versions(index: RevisionIndex) -> Callable[[date, str], list[dict]]:
    """The later A11 versions known now of a day's input (recorded in the day's provenance, never used)."""

    def lookup(day: date, label: str) -> list[dict]:
        found = index.for_path(VERSIONED_SOURCES[label].path_for(day))
        return [{"sha256": r.sha256, "available_from": r.available_from.isoformat()} for r in found]

    return lookup


def build_panel_day_job(env=os.environ) -> PanelDayJob:
    """Story A13: A3's builder on the first archived F&O and index-close files in Drive, appended to the panel folder,
    only under G1 protocol v3's freeze."""
    fo_files, index_files = first_archived_inputs(_project_drive(env))
    calendar = storage.build_session_calendar()
    builder = NiftyPanelBuilder(fo_files, index_files, calendar, storage.build_file_exceptions())
    lookup = later_versions(storage.build_revision_index())
    return PanelDayJob(builder, PanelAppender(storage.PANEL_FOLDER), calendar, require_v3_frozen, lookup,
                       build_alert_sender(), now_ist)  # fmt: skip
