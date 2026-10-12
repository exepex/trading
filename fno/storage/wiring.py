"""Composition root for raw data: the only place that picks concrete stores and sources (the app's services are
wired in fno/composition.py). Swapping Google Drive or NSE for something else changes this file only."""

from __future__ import annotations

import os
from pathlib import Path

from ..constants import ENV_GDRIVE_FOLDER_ID, ENV_GDRIVE_SERVICE_ACCOUNT_JSON, RESEARCH_USER_AGENT
from ..fo_bhavcopy import BadFile, read_fo_file, read_index_closes
from ..http_pacing import PacedSession
from ..research_data.calendar import load_session_calendar
from .coverage import CoverageCheck, CoverageDataset, read_exceptions
from .google_drive import GoogleDriveStore, service_account_token
from .raw_library import RawFileLibrary
from .raw_source import NseArchiveSource, NseDailyFoSource, NseIndexCloseSource, NseLegacyFoSource
from .raw_store import AreaStore, LocalFolderStore, RawFileStore

RAW_AREA = "raw"  # original downloads; other kinds of files get their own area next to it
CALENDAR_FOLDER = Path(__file__).resolve().parents[2] / "research" / "data" / "calendar"
COVERAGE_EXCEPTIONS = CALENDAR_FOLDER / "exceptions.csv"
REQUIRED_INDICES = ("Nifty 50", "India VIX")  # the research needs both from every index-close file


def build_raw_stores(project_folder: Path | None = None, token_for=service_account_token) -> list[RawFileStore]:
    """Where raw files are looked for, in order: the `raw` area of a local (Drive-synced) project folder, then of the
    shared Google Drive project folder if set up."""
    stores: list[RawFileStore] = [AreaStore(LocalFolderStore(project_folder), RAW_AREA)] if project_folder else []
    key, folder = os.environ.get(ENV_GDRIVE_SERVICE_ACCOUNT_JSON), os.environ.get(ENV_GDRIVE_FOLDER_ID)
    if key and folder:
        stores.append(AreaStore(GoogleDriveStore(folder, token_for(key)), RAW_AREA))
    return stores


def build_nse_library(source_type: type[NseArchiveSource], project_folder: Path | None = None) -> RawFileLibrary:
    """One NSE dataset: from the stores if they have it, else from NSE (saved under the local project folder's `raw`
    area if given)."""
    archive = AreaStore(LocalFolderStore(project_folder), RAW_AREA) if project_folder else None
    session = PacedSession()
    session.headers["User-Agent"] = RESEARCH_USER_AGENT  # NSE refuses the default python-requests identity
    return RawFileLibrary(build_raw_stores(project_folder), source_type(session), archive)


def build_nse_fo_library(project_folder: Path | None = None) -> RawFileLibrary:
    """NSE daily F&O files in the current (UDiFF) format, January 2024 onwards."""
    return build_nse_library(NseDailyFoSource, project_folder)


def build_nse_legacy_fo_library(project_folder: Path | None = None) -> RawFileLibrary:
    """NSE daily F&O files in the older format, up to 5 July 2024."""
    return build_nse_library(NseLegacyFoSource, project_folder)


def build_nse_index_close_library(project_folder: Path | None = None) -> RawFileLibrary:
    """NSE daily index closing values (NIFTY 50, India VIX and others)."""
    return build_nse_library(NseIndexCloseSource, project_folder)


QUOTES_FOLDER = (
    Path(__file__).resolve().parents[2] / "research" / "data" / "quotes"
)  # repository: Drive is read-only here


def build_quote_store(folder: Path | None = None) -> RawFileStore:
    """Where the 3 pm quote snapshots are written: a folder in the repository (committed daily)."""
    return LocalFolderStore(folder or QUOTES_FOLDER)


def validate_index_close(filename: str, data: bytes) -> None:
    missing = [name for name in REQUIRED_INDICES if name not in read_index_closes(data, filename)]
    if missing:
        raise BadFile(f"{filename}: no closing value for {missing}")


COVERAGE_DATASETS = (
    CoverageDataset(NseLegacyFoSource, read_fo_file),
    CoverageDataset(NseDailyFoSource, read_fo_file),
    CoverageDataset(NseIndexCloseSource, validate_index_close),
)


def build_coverage_check(store: RawFileStore | None = None) -> CoverageCheck:
    """The coverage check of the shared Drive project folder's `raw` area (read-only), or of the given store."""
    if store is None:
        stores = build_raw_stores()
        if not stores:
            raise RuntimeError(f"set {ENV_GDRIVE_SERVICE_ACCOUNT_JSON} and {ENV_GDRIVE_FOLDER_ID} to check Drive")
        store = stores[-1]
    return CoverageCheck(store, load_session_calendar(), read_exceptions(COVERAGE_EXCEPTIONS))
