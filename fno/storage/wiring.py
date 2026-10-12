"""Composition root for raw data: the only place that picks concrete stores and sources (the live desk's is
fno/live/services.py). Swapping Google Drive or NSE for something else changes this file only."""

from __future__ import annotations

import os
from pathlib import Path

from ..constants import ENV_GDRIVE_FOLDER_ID, ENV_GDRIVE_SERVICE_ACCOUNT_JSON
from ..http_pacing import PacedSession
from .google_drive import GoogleDriveStore, service_account_token
from .raw_library import RawFileLibrary
from .raw_source import NseDailyFoSource
from .raw_store import LocalFolderStore, RawFileStore


def build_raw_stores(keep_raw: Path | None = None, token_for=service_account_token) -> list[RawFileStore]:
    """Where raw files are looked for, in order: a local (Drive-synced) folder, then Google Drive if set up."""
    stores: list[RawFileStore] = [LocalFolderStore(keep_raw)] if keep_raw else []
    key, folder = os.environ.get(ENV_GDRIVE_SERVICE_ACCOUNT_JSON), os.environ.get(ENV_GDRIVE_FOLDER_ID)
    if key and folder:
        stores.append(GoogleDriveStore(folder, token_for(key)))
    return stores


def build_nse_fo_library(keep_raw: Path | None = None) -> RawFileLibrary:
    """NSE daily F&O files: from the stores if they have them, else from NSE (saved into `keep_raw` if given)."""
    archive = LocalFolderStore(keep_raw) if keep_raw else None
    return RawFileLibrary(build_raw_stores(keep_raw), NseDailyFoSource(PacedSession()), archive)
