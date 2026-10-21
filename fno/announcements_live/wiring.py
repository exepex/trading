"""Composition root of the same-day announcements poll (story A21 part 2): NSE's day list over a paced session, O9's
Drive store, part tables and verified cache, O10's capture-error log, #fno-desk alerts and A7's session calendar. A16's
wiring adds the poller to its mark observer group with `MEMBER_TIME_LIMIT_SECONDS`."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..alerts.sender import NoAlertSender
from ..composition import build_alert_sender
from ..config import ROOT
from ..health.capture_errors import CAPTURE_ERRORS_FILE, CaptureErrorLog
from ..intraday.observer import MarkObserver
from ..models import IST
from ..rates.failures import CaptureErrorFailures, run_url
from ..storage.data_store import DataStore, new_run_id
from ..storage.data_wiring import DATA_AREA, DRIVE_CACHE_FOLDER, RECEIPTS_FOLDER, build_data_store, build_drive_cache
from ..storage.drive_cache import DriveCache
from ..storage.raw_store import LocalFolderStore
from ..storage.receipts import ReceiptFolder
from ..storage.wiring import build_session_calendar
from .constants import ITEM_COLUMNS, ITEMS_TABLE, JOB, POLL_COLUMNS, POLLS_TABLE, WRITER
from .day_state import DayState, DriveDayState
from .mark_parts import MarkParts
from .poller import AnnouncementsPoller
from .source import NseDayList

DRY_RUN_FOLDER = ROOT / "work" / "announcements-dry-run"  # git-ignored: a local Drive, receipts and error log
DRY_RUN = "dry run: nothing posted"
# What the poller leaves in the checkout for A16's mark commit to carry: its Drive receipts and its O10 rows
COMMIT_PATHS = (f"{RECEIPTS_FOLDER}/{DATA_AREA}/announcements", CAPTURE_ERRORS_FILE)


def _now() -> datetime:
    return datetime.now(IST)


def _parts(store: DataStore, cache: DriveCache, folder: Path, log: Path, alerts) -> AnnouncementsPoller:
    failures = CaptureErrorFailures(CaptureErrorLog(log), run_url(), JOB)
    poller = AnnouncementsPoller(NseDayList(_now), DriveDayState(cache, DATA_AREA, folder), store,
                               MarkParts(store, ITEMS_TABLE, ITEM_COLUMNS), MarkParts(store, POLLS_TABLE, POLL_COLUMNS),
                                 failures, alerts, build_session_calendar().is_session, _now, store.run_id)  # fmt: skip
    poller.paths = COMMIT_PATHS
    return poller


def build_announcements_poller(dry_run: bool = False) -> AnnouncementsPoller:
    if not dry_run:
        return _parts(build_data_store(WRITER), build_drive_cache(), ROOT / DRIVE_CACHE_FOLDER / "announcements",
                      ROOT / CAPTURE_ERRORS_FILE, build_alert_sender())  # fmt: skip
    drive, receipts = LocalFolderStore(DRY_RUN_FOLDER / "drive"), ReceiptFolder(DRY_RUN_FOLDER / "receipts")
    store = DataStore(drive, DATA_AREA, receipts, WRITER, new_run_id())
    cache = DriveCache(drive, receipts, DRY_RUN_FOLDER / "cache")
    return _parts(store, cache, DRY_RUN_FOLDER / "cache", DRY_RUN_FOLDER / "errors.csv", NoAlertSender(DRY_RUN))


def day_state(day, dry_run: bool = False) -> DayState:
    """Today's items and polls, read back the way a new run reads them (through the Drive cache)."""
    return build_announcements_poller(dry_run).days.load(day)


NOT_BUILT = "the same-day announcements poll could not start ({error}); no poll today until it can"


class LazyAnnouncementsPoller(MarkObserver):
    """The member A16's group holds: it builds the poller at its first mark, inside the group's isolation and time
    limit, so a missing Drive setting can never stop A16's own recorder from being built. A build failure is one O10 row
    and one alert a day, and is raised again so the group names it."""

    def __init__(self, dry_run: bool = False):
        self.dry_run, self.poller, self.paths = dry_run, None, COMMIT_PATHS

    def after_mark(self, day, mark, document, status) -> None:
        if self.poller is None:
            try:
                self.poller = build_announcements_poller(self.dry_run)
            except Exception as error:
                self._not_built(day, type(error).__name__)
                raise
        self.poller.after_mark(day, mark, document, status)

    def _not_built(self, day, error: str) -> None:
        failures = CaptureErrorFailures(CaptureErrorLog(DRY_RUN_FOLDER / "errors.csv" if self.dry_run else
                                                        ROOT / CAPTURE_ERRORS_FILE), run_url(), JOB)  # fmt: skip
        if not failures.has(day, "not_built"):
            line = NOT_BUILT.format(error=error)
            failures.record(day, "build", "not_built", line)
            (NoAlertSender(DRY_RUN) if self.dry_run else build_alert_sender()).send(f"Omenix F&O (story A21): {line}")
