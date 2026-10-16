"""The position monitor's composition root (story LM1). A16's recorder takes `build_monitor_observer` in place of its
`NoObserver` when the first paper or shadow position is expected (the start condition; not before), with its own
folder, so a dry run of the recorder writes the monitor's rows under the same dry-run folder."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ..alerts.sender import AlertSender, NoAlertSender
from ..config import ROOT
from ..constants import PAPER_AREA
from ..desk.timetable import timetable_from_config
from ..intraday.heartbeat import Heartbeat
from ..intraday.ledger import SlotLedger
from ..models import now_ist
from ..research_data.calendar import load_session_calendar
from ..storage.index_store import DriveIndexStore, IndexFileStore, LocalIndexStore
from ..storage.wiring import CALENDAR_FILE, OWNER_UPLOAD_SETTINGS, build_drive_reader, build_owner_drive
from .alert_records import AlertRecords
from .alerting import MonitorAlerting
from .checks import BigMove, ExitRuleReached, ExpiryNear, LossUsed, QuotesStale, ShortStrikeNear
from .heartbeat import MonitorHeartbeat, MonitorSilence
from .limits import AlertLimits
from .mark_reader import ArchivedNiftyCloses, MarkReader, PreviousCloses
from .mark_rows import MarkRows
from .monitor import PositionMonitor
from .observer import MonitorObserver
from .positions import NoOpenPositions
from .settings import MonitorSettings

MONITOR_FOLDER = "monitor"  # inside A16's intraday folder: the rows and heartbeat go up in A16's commit
DRY_RUN_PRIVATE = "private"  # inside a dry-run folder: stands in for Drive's paper area
DRY_RUN_ALERTS = "dry run"
NO_DRIVE = "the owner's Drive settings are missing ({settings})"
# The monitor's time per mark in A16's ObserverGroup (63d8de75: per-member limits, cap 300 s): one Slack post may take
# its full 15 s timeout and a stress day sends several DANGERs on one mark; marks are 15 minutes apart
MONITOR_TIME_LIMIT_SECONDS = 90.0


def monitor_settings(cfg: dict) -> MonitorSettings:
    return MonitorSettings.from_config(cfg["monitor"], timetable_from_config(cfg).execution_snapshot)


def build_position_monitor(cfg: dict) -> PositionMonitor:
    settings = monitor_settings(cfg)
    checks = [LossUsed(settings), ShortStrikeNear(settings), ExitRuleReached(settings), BigMove(settings),
              ExpiryNear(settings, load_session_calendar(CALENDAR_FILE))]  # fmt: skip
    return PositionMonitor(settings, checks, QuotesStale(settings))


def build_alert_limits(cfg: dict) -> AlertLimits:
    return AlertLimits(monitor_settings(cfg))


def monitor_alerts() -> AlertSender:
    """The monitor's alert path: the one existing sender. O1's `ReportedAlerts` wraps it here when O1 merges (one
    line, no second wrapper). Imported here, not at the top: the app's composition root also builds the books'
    services, and nothing of them belongs in the monitor's imports (criterion 1); only the sender is taken."""
    from ..composition import build_alert_sender

    return build_alert_sender()


def build_monitor_observer(cfg: dict, intraday_folder: Path, dry_run: bool = False) -> MonitorObserver:
    settings = monitor_settings(cfg)
    folder = Path(intraday_folder) / MONITOR_FOLDER
    reader = MarkReader(SlotLedger(intraday_folder), _closes(), load_session_calendar(CALENDAR_FILE), settings)
    private = LocalIndexStore(Path(intraday_folder) / DRY_RUN_PRIVATE) if dry_run else _paper_area()
    alerts = NoAlertSender(DRY_RUN_ALERTS) if dry_run else monitor_alerts()
    alerting = MonitorAlerting(AlertLimits(settings), AlertRecords(private, ROOT), alerts, settings, now_ist)
    return MonitorObserver(NoOpenPositions(), reader, build_position_monitor(cfg), alerting, MarkRows(folder),
                           MonitorHeartbeat(Heartbeat(folder)), now_ist)  # fmt: skip


def build_monitor_silence(intraday_folder: Path, heartbeat=None) -> MonitorSilence:
    """`heartbeat`: the reader to check (A16 passes GitHub's copy, `PublishedHeartbeat`); default the local file."""
    calendar = load_session_calendar(CALENDAR_FILE)
    reader = heartbeat or Heartbeat(Path(intraday_folder) / MONITOR_FOLDER)
    return MonitorSilence(reader, lambda day: _recorded(calendar, day))


def _recorded(calendar, day: date) -> bool:
    from ..quotes.recorder import RECORDED_SESSION_KINDS

    return calendar.session_kind(day) in RECORDED_SESSION_KINDS


def _closes() -> PreviousCloses:
    try:
        return ArchivedNiftyCloses(build_drive_reader())
    except RuntimeError:
        return _NoCloses()


class _NoCloses(PreviousCloses):
    """Drive's raw area is not set up: the close is unknown, the mark row says so (`previous_close_known`)."""

    def close(self, day: date) -> float | None:
        return None


def _paper_area() -> IndexFileStore:
    drive = build_owner_drive()
    if drive is None:
        raise RuntimeError(NO_DRIVE.format(settings=", ".join(OWNER_UPLOAD_SETTINGS)))
    return DriveIndexStore(drive, PAPER_AREA)
