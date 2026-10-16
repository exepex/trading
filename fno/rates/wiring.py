"""Composition root of the rates capture (story A21): RBI over HTTP, O9's Drive store, part table, cache and receipts,
O10's capture-error log and the #fno-desk alert sender."""

from __future__ import annotations

from datetime import datetime

from ..alerts.sender import NoAlertSender
from ..composition import build_alert_sender
from ..config import ROOT
from ..health.capture_errors import CAPTURE_ERRORS_FILE, CaptureErrorLog
from ..models import IST
from ..storage.data_store import DataStore, new_run_id
from ..storage.data_wiring import DATA_AREA, DRIVE_CACHE_FOLDER, build_data_store, build_drive_cache, receipt_folder
from ..storage.drive_cache import DriveCache
from ..storage.part_table import PartTable
from ..storage.raw_store import LocalFolderStore
from ..storage.receipts import ReceiptFolder
from .as_of import RatesAsOf
from .capture import RatesCapture
from .constants import COLUMNS, TABLE, WRITER
from .failures import CaptureErrorFailures, run_url
from .fetch import RbiPages
from .history import DriveRatesHistory

DRY_RUN_FOLDER = ROOT / "work" / "rates-dry-run"  # git-ignored: a local Drive, receipts and error log, nothing sent
DRY_RUN = "dry run: nothing posted"


def _history(cache=None, receipts=None, into=None) -> DriveRatesHistory:
    return DriveRatesHistory(cache or build_drive_cache(), receipts or receipt_folder(), DATA_AREA,
                             into or ROOT / DRIVE_CACHE_FOLDER / "rates")  # fmt: skip


def _dry_run_parts():
    drive, receipts = LocalFolderStore(DRY_RUN_FOLDER / "drive"), ReceiptFolder(DRY_RUN_FOLDER / "receipts")
    store = DataStore(drive, DATA_AREA, receipts, WRITER, new_run_id())
    history = _history(DriveCache(drive, receipts, DRY_RUN_FOLDER / "cache"), receipts, DRY_RUN_FOLDER / "table")
    return store, history, DRY_RUN_FOLDER / "errors.csv", NoAlertSender(DRY_RUN)


def _live_parts():
    return build_data_store(WRITER), _history(), ROOT / CAPTURE_ERRORS_FILE, build_alert_sender()


def build_rates_capture(dry_run: bool = False) -> RatesCapture:
    """Live: the owner's Drive, the committed receipts and O10's log, alerts to #fno-desk. Dry run: the same code on a
    local folder standing in for Drive, its own receipts and error log, and no alert sent."""
    store, history, log, alerts = _dry_run_parts() if dry_run else _live_parts()
    failures = CaptureErrorFailures(CaptureErrorLog(log), run_url())
    return RatesCapture(RbiPages(), store, PartTable(store, TABLE, COLUMNS), history, failures, alerts,
                        lambda: datetime.now(IST))  # fmt: skip


def build_rates_as_of() -> RatesAsOf:
    return RatesAsOf(_history().rows())
