"""Composition root for raw data: the only place that picks concrete stores and sources (the app's services are
wired in fno/composition.py). Swapping Google Drive or NSE for something else changes this file only."""

from __future__ import annotations

import os
from pathlib import Path

from ..constants import (
    ENV_GDRIVE_FOLDER_ID,
    ENV_GDRIVE_SERVICE_ACCOUNT_JSON,
    INDEX_INDIA_VIX,
    INDEX_NIFTY_50,
    PANEL_FORMAT_LEGACY,
    PANEL_FORMAT_UDIFF,
    PANEL_INDEX_CLOSE,
    RESEARCH_USER_AGENT,
)
from ..fo_bhavcopy import BadFile, read_fo_file, read_index_closes
from ..http_pacing import PacedSession
from ..research_data.calendar import SessionCalendar, load_session_calendar
from ..research_data.nifty_panel import DailyFiles
from ..research_data.panel_store import CsvGzPanelFolder, PanelSink
from ..research_data.participant_oi import read_participant_oi
from .coverage import CoverageCheck, CoverageDataset, FingerprintCheck, read_exceptions, read_fingerprints
from .google_drive import GoogleDriveStore, service_account_token
from .raw_library import RawFileLibrary
from .raw_source import (
    NseArchiveSource,
    NseDailyFoSource,
    NseIndexCloseSource,
    NseLegacyFoSource,
    ParticipantOiSource,
)
from .raw_store import AreaStore, LocalFolderStore, RawFileStore

RAW_AREA = "raw"  # original downloads; other kinds of files get their own area next to it
CALENDAR_FOLDER = Path(__file__).resolve().parents[2] / "research" / "data" / "calendar"
CALENDAR_FILE = CALENDAR_FOLDER / "nse_sessions.csv"  # NSE's sessions, from its circulars (SessionCalendar)
COVERAGE_EXCEPTIONS = CALENDAR_FOLDER / "exceptions.csv"
REQUIRED_INDICES = (INDEX_NIFTY_50, INDEX_INDIA_VIX)
LAPTOP_TOOL_FOLDER = Path(__file__).resolve().parents[2] / "tools" / "nse_raw_download"
PARTICIPANT_OI_MANIFEST = LAPTOP_TOOL_FOLDER / "manifest_participant_oi.csv"  # SHA-256 of NSE's files (story A8)


def build_raw_stores(project_folder: Path | None = None, token_for=service_account_token) -> list[RawFileStore]:
    """Where raw files are looked for, in order: the `raw` area of a local (Drive-synced) project folder, then of the
    shared Google Drive project folder if set up."""
    stores: list[RawFileStore] = [AreaStore(LocalFolderStore(project_folder), RAW_AREA)] if project_folder else []
    key, folder = os.environ.get(ENV_GDRIVE_SERVICE_ACCOUNT_JSON), os.environ.get(ENV_GDRIVE_FOLDER_ID)
    if key and folder:
        stores.append(AreaStore(GoogleDriveStore(folder, lambda: token_for(key)), RAW_AREA))
    return stores


def build_nse_library(source_type: type[NseArchiveSource], project_folder: Path | None = None) -> RawFileLibrary:
    """One NSE dataset: from the stores if they have it, else from NSE (saved under the local project folder's `raw`
    area if given)."""
    archive = AreaStore(LocalFolderStore(project_folder), RAW_AREA) if project_folder else None
    return RawFileLibrary(build_raw_stores(project_folder), build_nse_source(source_type), archive)


def build_nse_source(source_type: type[NseArchiveSource]) -> NseArchiveSource:
    """One NSE dataset straight from NSE's archive, through the shared polite session."""
    session = PacedSession()
    session.headers["User-Agent"] = RESEARCH_USER_AGENT  # NSE refuses the default python-requests identity
    return source_type(session)


def build_nse_fo_library(project_folder: Path | None = None) -> RawFileLibrary:
    """NSE daily F&O files in the current (UDiFF) format, January 2024 onwards."""
    return build_nse_library(NseDailyFoSource, project_folder)


def build_nse_legacy_fo_library(project_folder: Path | None = None) -> RawFileLibrary:
    """NSE daily F&O files in the older format, up to 5 July 2024."""
    return build_nse_library(NseLegacyFoSource, project_folder)


def build_nse_index_close_library(project_folder: Path | None = None) -> RawFileLibrary:
    """NSE daily index closing values (NIFTY 50, India VIX and others)."""
    return build_nse_library(NseIndexCloseSource, project_folder)


def build_participant_oi_library(project_folder: Path | None = None) -> RawFileLibrary:
    """NSE daily participant-wise open interest (story A8)."""
    return build_nse_library(ParticipantOiSource, project_folder)


QUOTES_FOLDER = (
    Path(__file__).resolve().parents[2] / "research" / "data" / "quotes"
)  # repository: Drive is read-only here


PARTICIPANT_OI_RELEASE_LOG = (
    Path(__file__).resolve().parents[2] / "research" / "data" / "participant_oi" / "release_checks.csv"
)  # repository: the committed evidence of NSE's release times (story A8)


def build_quote_store(folder: Path | None = None) -> RawFileStore:
    """Where the 3 pm quote snapshots are written: a folder in the repository (committed daily)."""
    return LocalFolderStore(folder or QUOTES_FOLDER)


def validate_index_close(filename: str, data: bytes) -> None:
    missing = [name for name in REQUIRED_INDICES if name not in read_index_closes(data, filename)]
    if missing:
        raise BadFile(f"{filename}: no closing value for {missing}")


def validate_participant_oi(filename: str, data: bytes) -> None:
    read_participant_oi(data, filename, ParticipantOiSource.day_for(filename))


COVERAGE_DATASETS = (
    CoverageDataset(NseLegacyFoSource, read_fo_file),
    CoverageDataset(NseDailyFoSource, read_fo_file),
    CoverageDataset(NseIndexCloseSource, validate_index_close),
    CoverageDataset(
        ParticipantOiSource, FingerprintCheck(validate_participant_oi, read_fingerprints(PARTICIPANT_OI_MANIFEST))
    ),
)


def build_coverage_check(store: RawFileStore | None = None) -> CoverageCheck:
    """The coverage check of the shared Drive project folder's `raw` area (read-only), or of the given store."""
    if store is None:
        stores = build_raw_stores()
        if not stores:
            raise RuntimeError(f"set {ENV_GDRIVE_SERVICE_ACCOUNT_JSON} and {ENV_GDRIVE_FOLDER_ID} to check Drive")
        store = stores[-1]
    return CoverageCheck(store, build_session_calendar(), build_file_exceptions())


PANEL_FOLDER = Path(__file__).resolve().parents[2] / "research" / "data" / "nifty-panel"  # story A3's output


def daily_files(label: str, source_type: type[NseArchiveSource], library: RawFileLibrary) -> DailyFiles:
    """A day's original file name and bytes from a raw-file library (stores first, then NSE; Drive is only read)."""
    return DailyFiles(
        label,
        source_type.dataset,
        source_type.first_day,
        source_type.last_day,
        lambda day: (source_type.filename_for(day), library.get(source_type.path_for(day)).data),
    )


def build_nifty_panel_files(project_folder: Path | None = None) -> tuple[list[DailyFiles], DailyFiles]:
    """The NIFTY panel's inputs: F&O files in order of precedence (current format first), and index closes."""
    fo_files = [
        daily_files(PANEL_FORMAT_UDIFF, NseDailyFoSource, build_nse_fo_library(project_folder)),
        daily_files(PANEL_FORMAT_LEGACY, NseLegacyFoSource, build_nse_legacy_fo_library(project_folder)),
    ]
    return fo_files, daily_files(PANEL_INDEX_CLOSE, NseIndexCloseSource, build_nse_index_close_library(project_folder))


def build_panel_sink(folder: Path | None = None) -> PanelSink:
    return CsvGzPanelFolder(folder or PANEL_FOLDER)


def build_session_calendar() -> SessionCalendar:
    """NSE's sessions from the repository's calendar file: the one answer to "is this day a session"."""
    return load_session_calendar(CALENDAR_FILE)


def build_file_exceptions() -> dict:
    """(dataset, day) -> reason, for sessions NSE never published a file for (sourced; A1)."""
    return read_exceptions(COVERAGE_EXCEPTIONS)
