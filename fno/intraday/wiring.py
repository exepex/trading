"""Composition root of the 15-minute recorder (story A16): the only place that picks Groww, the owner's Drive, the
repository folder, the clock servers, the alert sender and the publisher. Swapping the source is one new
`IntradayQuoteSource` class plus one line here.

A dry run reads Groww live but writes the raw snapshots, ledger, realised variance and heartbeat under a local folder
outside the repository, sends no alert and commits nothing."""

from __future__ import annotations

from pathlib import Path

from ..alerts.sender import AlertSender, NoAlertSender
from ..composition import build_alert_sender
from ..providers.groww import GrowwProvider
from ..quotes.expiry_listing import NseDailyFileExpiries
from ..quotes.monthly_contracts import PointInTimeMonthlies
from ..storage.manifest_commit import GitManifestRecorder, ManifestRecorder
from ..storage.raw_store import AreaStore, LocalFolderStore, RawFileStore
from ..storage.wiring import (
    OWNER_UPLOAD_SETTINGS,
    RAW_AREA,
    REPOSITORY,
    REVISIONS_AREA,
    build_nse_fo_library,
    build_owner_drive,
    build_session_calendar,
)
from .clock import GITHUB_TIME_URL, SLACK_TIME_URL, ClockCheck, HttpDateClock
from .dry_run import NoPublish
from .expiry_plan import UNDERLYING, ExpiryPlan
from .first_version_store import FirstVersionStore
from .groww_source import GrowwIntradaySource
from .heartbeat import Heartbeat
from .ledger import SlotLedger
from .realised_vol import QuoteSnapshotRv15m
from .recorder import IntradayRecorder
from .rv_table import RvTable
from .session_rv import SessionRv

INTRADAY_FOLDER = REPOSITORY / "research" / "data" / "intraday"  # derived files only: no prices
REVISION_INDEX = "revisions.csv"  # A11's index of later versions of a snapshot path, beside the ledger
DRY_RUN_DRIVE = "drive"  # inside a dry-run folder: stands in for the Drive project folder
COMMIT_MESSAGE = "Data: intraday slots ({what})"
DRY_RUN_ALERTS = "dry run"


def build_intraday_recorder(cfg: dict, dry_run_folder: Path | None = None) -> IntradayRecorder:
    folder = Path(dry_run_folder) if dry_run_folder else INTRADAY_FOLDER
    store = _snapshot_store(folder, dry_run_folder is not None)
    provider = GrowwProvider(cfg)
    source = GrowwIntradaySource(provider, _expiry_plan(provider))
    calendar = build_session_calendar()
    session_rv = SessionRv(store, source.name, calendar, RvTable(folder), QuoteSnapshotRv15m())
    clock = ClockCheck([HttpDateClock("github", GITHUB_TIME_URL), HttpDateClock("slack", SLACK_TIME_URL)])
    return IntradayRecorder(
        source, store, SlotLedger(folder), Heartbeat(folder), calendar, _alerts(dry_run_folder), clock, session_rv,
        _publisher(dry_run_folder),
    )  # fmt: skip


def build_heartbeat() -> Heartbeat:
    return Heartbeat(INTRADAY_FOLDER)


def _snapshot_store(folder: Path, dry_run: bool) -> RawFileStore:
    """The owner's Drive (A9), raw area plus A11's revisions area; in a dry run, a local folder of the same shape."""
    drive = LocalFolderStore(folder / DRY_RUN_DRIVE) if dry_run else build_owner_drive()
    if drive is None:
        raise RuntimeError(f"set {', '.join(OWNER_UPLOAD_SETTINGS)} to store snapshots in Drive")
    raw, revisions = AreaStore(drive, RAW_AREA), AreaStore(drive, REVISIONS_AREA)
    return FirstVersionStore(raw, revisions, folder / REVISION_INDEX)


def _expiry_plan(provider: GrowwProvider) -> ExpiryPlan:
    """Groww's list first; NSE's daily files for what Groww cannot list and to prove the monthly (as A4)."""
    nse = NseDailyFileExpiries(build_nse_fo_library())
    return ExpiryPlan(lambda: provider.expiries(UNDERLYING), nse, PointInTimeMonthlies(nse))


def _alerts(dry_run_folder: Path | None) -> AlertSender:
    return NoAlertSender(DRY_RUN_ALERTS) if dry_run_folder else build_alert_sender()


def _publisher(dry_run_folder: Path | None) -> ManifestRecorder:
    return NoPublish() if dry_run_folder else GitManifestRecorder(REPOSITORY, INTRADAY_FOLDER, message=COMMIT_MESSAGE)
