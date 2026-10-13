"""Composition root for raw data: the only place that picks concrete stores and sources (the app's services are
wired in fno/composition.py). Swapping Google Drive or NSE for something else changes this file only."""

from __future__ import annotations

import os
from pathlib import Path

from ..constants import (
    ENV_GDRIVE_FOLDER_ID,
    ENV_GDRIVE_OAUTH_CLIENT_ID,
    ENV_GDRIVE_OAUTH_CLIENT_SECRET,
    ENV_GDRIVE_OAUTH_REFRESH_TOKEN,
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
from .coverage import CoverageCheck, CoverageDataset, read_exceptions
from .google_drive import GoogleDriveStore, service_account_token
from .google_drive_upload import GoogleDriveUploadStore
from .librarian import RawDataLibrarian
from .manifest_commit import GitManifestRecorder, ManifestRecorder
from .manifest_folder import FingerprintingStore, ManifestFolder
from .owner_token import OwnerAccessToken
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
REPOSITORY = Path(__file__).resolve().parents[2]
MANIFEST_FOLDER = REPOSITORY / "research" / "data" / "manifests"  # SHA-256 per file (A10)
RAW_SOURCES = (NseLegacyFoSource, NseDailyFoSource, NseIndexCloseSource, ParticipantOiSource)


def build_raw_stores(project_folder: Path | None = None, token_for=service_account_token) -> list[RawFileStore]:
    """Where raw files are looked for, in order: the `raw` area of a local (Drive-synced) project folder, then of the
    shared Google Drive project folder if set up."""
    stores: list[RawFileStore] = [AreaStore(LocalFolderStore(project_folder), RAW_AREA)] if project_folder else []
    key, folder = os.environ.get(ENV_GDRIVE_SERVICE_ACCOUNT_JSON), os.environ.get(ENV_GDRIVE_FOLDER_ID)
    if key and folder:
        stores.append(AreaStore(GoogleDriveStore(folder, lambda: token_for(key)), RAW_AREA))
    return stores


OWNER_UPLOAD_SETTINGS = (
    ENV_GDRIVE_FOLDER_ID,
    ENV_GDRIVE_OAUTH_CLIENT_ID,
    ENV_GDRIVE_OAUTH_CLIENT_SECRET,
    ENV_GDRIVE_OAUTH_REFRESH_TOKEN,
)


def build_owner_drive_store(env=os.environ, session=None) -> RawFileStore | None:
    """The `raw` area of the Drive project folder, written as the owner (story A9); None unless all four settings
    are set. Signs in at once, so an expired consent shows up here as DriveSignInRefused."""
    folder, client_id, client_secret, refresh_token = (env.get(name) for name in OWNER_UPLOAD_SETTINGS)
    if not (folder and client_id and client_secret and refresh_token):
        return None
    token = OwnerAccessToken(client_id, client_secret, refresh_token)
    drive = AreaStore(GoogleDriveUploadStore(folder, token, session), RAW_AREA)
    return FingerprintingStore(drive, build_manifest_folder(), RAW_SOURCES)  # every saved file gets its manifest row


def build_manifest_folder() -> ManifestFolder:
    return ManifestFolder(MANIFEST_FOLDER)


def build_manifest_recorder() -> ManifestRecorder:
    """Commits the manifest rows of this repository (git, with its hooks)."""
    return GitManifestRecorder(REPOSITORY, MANIFEST_FOLDER)


def build_nse_library(source_type: type[NseArchiveSource], project_folder: Path | None = None) -> RawFileLibrary:
    """One NSE dataset: from the stores if they have it, else from NSE. What it fetches is archived straight to the
    owner's Drive when the upload settings exist, else under the local project folder's `raw` area if given."""
    archive = build_owner_drive_store()
    if archive is None and project_folder:
        archive = AreaStore(LocalFolderStore(project_folder), RAW_AREA)
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


PARTICIPANT_OI_EVIDENCE = Path(__file__).resolve().parents[2] / "research" / "data" / "participant_oi"
PARTICIPANT_OI_RELEASE_LOG = PARTICIPANT_OI_EVIDENCE / "release_checks.csv"  # NSE's release times, committed (A8)
PARTICIPANT_OI_LAST_MODIFIED = PARTICIPANT_OI_EVIDENCE / "archive_last_modified_2026-10-13.csv"  # with the download
PARTICIPANT_OI_SWEEPS = PARTICIPANT_OI_EVIDENCE / "last_modified_sweeps.csv"  # write times that moved later (judge 16)


def build_quote_store(folder: Path | None = None) -> RawFileStore:
    """Where the 3 pm quote snapshots are written: a folder in the repository (committed daily)."""
    return LocalFolderStore(folder or QUOTES_FOLDER)


def validate_index_close(filename: str, data: bytes) -> None:
    missing = [name for name in REQUIRED_INDICES if name not in read_index_closes(data, filename)]
    if missing:
        raise BadFile(f"{filename}: no closing value for {missing}")


def validate_participant_oi(filename: str, data: bytes) -> None:
    read_participant_oi(data, filename, ParticipantOiSource.day_for(filename))


VALIDATORS = {
    NseLegacyFoSource: read_fo_file,
    NseDailyFoSource: read_fo_file,
    NseIndexCloseSource: validate_index_close,
    ParticipantOiSource: validate_participant_oi,
}


def coverage_datasets(manifests: ManifestFolder | None = None) -> tuple[CoverageDataset, ...]:
    """Every raw dataset with its content check and its manifest's fingerprints (read now, never cached)."""
    manifests = manifests or build_manifest_folder()
    return tuple(CoverageDataset(s, VALIDATORS[s], manifests.fingerprints(s)) for s in RAW_SOURCES)


def dataset_name(source: type[NseArchiveSource]) -> str:
    return source.dataset.rsplit("/", 1)[-1]


# Datasets the librarian may upload: each new one needs its own story (A9: participant OI; A10: index closes).
LIBRARIAN_DATASETS = {dataset_name(s): s for s in (ParticipantOiSource, NseIndexCloseSource)}
FINGERPRINT_SOURCES = {dataset_name(s): s for s in RAW_SOURCES}


def build_librarian(name: str, log=print) -> RawDataLibrarian:
    """The librarian for one dataset (a key of LIBRARIAN_DATASETS): NSE's archive into the owner's Drive."""
    store = build_owner_drive_store()
    if store is None:
        raise RuntimeError(f"set {', '.join(OWNER_UPLOAD_SETTINGS)} to upload to Drive")
    source_type = LIBRARIAN_DATASETS[name]
    dataset = next(d for d in coverage_datasets() if d.source is source_type)
    source = build_nse_source(source_type)
    return RawDataLibrarian(store, source, dataset, build_session_calendar(), build_file_exceptions(), log)


def build_drive_reader() -> RawFileStore:
    """The shared Drive project folder's `raw` area, read with the service account."""
    stores = build_raw_stores()
    if not stores:
        raise RuntimeError(f"set {ENV_GDRIVE_SERVICE_ACCOUNT_JSON} and {ENV_GDRIVE_FOLDER_ID} to read Drive")
    return stores[-1]


def build_coverage_check(store: RawFileStore | None = None) -> CoverageCheck:
    """The coverage check of the shared Drive project folder's `raw` area (read-only), or of the given store."""
    return CoverageCheck(store or build_drive_reader(), build_session_calendar(), build_file_exceptions())


PANEL_FOLDER = Path(__file__).resolve().parents[2] / "research" / "data" / "nifty-panel"  # story A3's output
EVENTS_FILE = Path(__file__).resolve().parents[2] / "research" / "data" / "events" / "events.csv"  # story A6
LIVE_VALIDATION_FOLDER = Path(__file__).resolve().parents[2] / "research" / "live_validation"  # story B7 reports


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
    return fo_files, build_index_close_files(project_folder)


def build_index_close_files(project_folder: Path | None = None) -> DailyFiles:
    """NSE's daily index-close files (the panel's closes, and story A10's warm-up closes; never an F&O file)."""
    return daily_files(PANEL_INDEX_CLOSE, NseIndexCloseSource, build_nse_index_close_library(project_folder))


def build_panel_sink(folder: Path | None = None) -> PanelSink:
    return CsvGzPanelFolder(folder or PANEL_FOLDER)


def build_session_calendar() -> SessionCalendar:
    """NSE's sessions from the repository's calendar file: the one answer to "is this day a session"."""
    return load_session_calendar(CALENDAR_FILE)


def build_file_exceptions() -> dict:
    """(dataset, day) -> reason, for sessions NSE never published a file for (sourced; A1)."""
    return read_exceptions(COVERAGE_EXCEPTIONS)
