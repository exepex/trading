"""Composition root for raw data: the only place that picks concrete stores and sources (the live desk's is
fno/live/services.py). Swapping Google Drive or NSE for something else changes this file only."""

from __future__ import annotations

import os
from pathlib import Path

from ..constants import ENV_GDRIVE_FOLDER_ID, ENV_GDRIVE_SERVICE_ACCOUNT_JSON, RESEARCH_USER_AGENT
from ..http_pacing import PacedSession
from .google_drive import GoogleDriveStore, service_account_token
from .raw_library import RawFileLibrary
from .raw_source import NseDailyFoSource
from .raw_store import AreaStore, LocalFolderStore, RawFileStore

RAW_AREA = "raw"  # original downloads; other kinds of files get their own area next to it


def build_raw_stores(project_folder: Path | None = None, token_for=service_account_token) -> list[RawFileStore]:
    """Where raw files are looked for, in order: the `raw` area of a local (Drive-synced) project folder, then of the
    shared Google Drive project folder if set up."""
    stores: list[RawFileStore] = [AreaStore(LocalFolderStore(project_folder), RAW_AREA)] if project_folder else []
    key, folder = os.environ.get(ENV_GDRIVE_SERVICE_ACCOUNT_JSON), os.environ.get(ENV_GDRIVE_FOLDER_ID)
    if key and folder:
        stores.append(AreaStore(GoogleDriveStore(folder, token_for(key)), RAW_AREA))
    return stores


def build_nse_fo_library(project_folder: Path | None = None) -> RawFileLibrary:
    """NSE daily F&O files: from the stores if they have them, else from NSE (saved under the local project folder's
    `raw` area if given)."""
    archive = AreaStore(LocalFolderStore(project_folder), RAW_AREA) if project_folder else None
    session = PacedSession()
    session.headers["User-Agent"] = RESEARCH_USER_AGENT  # NSE refuses the default python-requests identity
    return RawFileLibrary(build_raw_stores(project_folder), NseDailyFoSource(session), archive)
