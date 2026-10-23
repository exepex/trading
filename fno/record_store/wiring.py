"""Composition root of story DR1's records: per dataset, its rules, where its versions come from and the shadow's
comparison; the owner's Drive project folder (read by path), the checkout's receipts and its `receipts/records/` tree
with a committer of that tree only. First dataset: A4h's closes, in shadow (A4h's raw answers as the versions).

The certifier only reads: the official index-close file comes from the stores (Drive, the local archive), never from
NSE. `build_index_close_files()` would fetch a file Drive lacks and archive it (its library's `archive`), a write a
certifier must never make (23 Oct: a dry run archived 23 Oct's file that way, manifest row aa0e2ed30)."""

from __future__ import annotations

import os

from ..close_read.official import ArchivedIndexCloses
from ..constants import PANEL_INDEX_CLOSE
from ..research_data.nifty_panel import DailyFiles
from ..storage.data_wiring import receipt_folder
from ..storage.manifest_commit import GitManifestRecorder
from ..storage.raw_source import NseIndexCloseSource
from ..storage.wiring import OWNER_UPLOAD_SETTINGS, REPOSITORY, build_owner_drive, build_raw_stores
from .certifier import Certifier
from .closes import DATASET as CLOSES
from .closes import A4hRecordComparison, ClosesRules, a4h_raw_paths
from .constants import RECORDS_FOLDER, RECORDS_LABEL, RECORDS_MESSAGE
from .reader import RecordReader
from .record_folder import RecordFolder
from .staging import ReceiptedFiles

DATASETS = (CLOSES,)


def _drive(env=os.environ):
    drive = build_owner_drive(env)
    if drive is None:
        raise RuntimeError(f"set {', '.join(OWNER_UPLOAD_SETTINGS)} to read the Drive data folder")
    return drive


def build_record_folder(commit: bool) -> RecordFolder:
    folder = REPOSITORY / RECORDS_FOLDER
    if not commit:
        return RecordFolder(folder)
    return RecordFolder(folder, GitManifestRecorder(REPOSITORY, folder, message=RECORDS_MESSAGE, label=RECORDS_LABEL))


def stored_index_closes(stores=None) -> DailyFiles:
    """NSE's index-close files as the stores hold them: a day no store has is None (not archived yet), never fetched."""
    stores = build_raw_stores() if stores is None else stores
    source = NseIndexCloseSource

    def get(day):
        path = source.path_for(day)
        return source.filename_for(day), next((d for d in (s.get(path) for s in stores) if d is not None), None)

    return DailyFiles(PANEL_INDEX_CLOSE, source.dataset, source.first_day, source.last_day, get)


def build_certifier(dataset: str, commit: bool, env=os.environ) -> Certifier:
    if dataset != CLOSES:
        raise ValueError(f"no certification rules for {dataset!r}; known: {', '.join(DATASETS)}")
    drive = _drive(env)
    rules = ClosesRules(ArchivedIndexCloses(stored_index_closes()))
    versions = ReceiptedFiles(receipt_folder(), a4h_raw_paths)
    return Certifier(rules, versions, drive, build_record_folder(commit), A4hRecordComparison(drive))


def build_record_reader(env=os.environ) -> RecordReader:
    return RecordReader(build_record_folder(commit=False), _drive(env))
