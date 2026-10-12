"""Composition root of the F&O app: the only place that picks concrete classes for the app's services (raw data stores
and sources are wired in `fno/storage/wiring.py`). Swapping a provider or store changes this file only."""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import time
from pathlib import Path

from .alerts.sender import AlertSender, NoAlertSender, SlackChannelAlerts
from .books.account import AccountWriter, PaperAccount
from .books.lock import DEFAULT_LEASE_SECONDS, AccountLock
from .config import ROOT
from .constants import ENV_FNO_SLACK_BOT_TOKEN, FNO_DESK_CHANNEL_ID
from .providers import AUTO_PROVIDER, get_provider
from .quotes.expiry_listing import NseDailyFileExpiries
from .quotes.recorder import QuoteSnapshotRecorder
from .record_scan.catalogue import ALLOWED_VALUES, credential_patterns, record_patterns
from .record_scan.scanner import RecordScanner
from .research_data.availability import AvailabilityRule
from .research_data.calendar import load_session_calendar
from .research_data.positioning import PointInTimeParticipantOi
from .research_data.release_times import ReleaseLog, ReleaseTimeRecorder, choose_availability_rule
from .storage.raw_source import ParticipantOiSource
from .storage.wiring import (
    CALENDAR_FILE,
    PARTICIPANT_OI_RELEASE_LOG,
    build_nse_fo_library,
    build_nse_source,
    build_participant_oi_library,
    build_quote_store,
)

DESK_DECISION_TIME = time(15, 0)  # design 13.5: books decide at about 15:00 IST; story E3 freezes the exact timetable


def build_quote_recorder(cfg: dict) -> QuoteSnapshotRecorder:
    """The 3 pm quote recorder (story A4): its own `quotes.provider` setting (`auto`: Groww when its credentials are
    set, else NSE), never the root `provider` used by the `chain` command; the repository quote store; and NSE's daily
    file for expiry dates the provider cannot list."""
    provider = get_provider(cfg.get("quotes", {}).get("provider", AUTO_PROVIDER), cfg)
    return QuoteSnapshotRecorder(provider, build_quote_store(), fallback=NseDailyFileExpiries(build_nse_fo_library()))


def build_record_scanner() -> RecordScanner:
    """The public-record scan (story O5): every pattern of the catalogue for records, credential shapes for code, with
    the #fno-desk channel ID allowed."""
    return RecordScanner(record_patterns(), ALLOWED_VALUES, credential_patterns())


@contextmanager
def open_account_writer(book: str, root: Path = ROOT, lease_seconds: float = DEFAULT_LEASE_SECONDS):
    """The one way to write a book's paper account (story E1): takes the book's single-writer lock without waiting
    (`AccountBusy` if another writer holds it) and yields the account's writer; the lock is released on exit."""
    with AccountLock(root, book, lease_seconds) as lock:
        yield AccountWriter(PaperAccount(root, book), lock)


def build_paper_account(book: str, root: Path = ROOT) -> PaperAccount:
    """Read-only view of a book's paper account."""
    return PaperAccount(root, book)


def build_alert_sender() -> AlertSender:
    """Alerts go to #fno-desk with `FNO_SLACK_BOT_TOKEN`; without it, nothing is sent and the outcome says so."""
    token = os.environ.get(ENV_FNO_SLACK_BOT_TOKEN)
    return SlackChannelAlerts(token, FNO_DESK_CHANNEL_ID) if token else NoAlertSender()


def build_release_time_recorder() -> ReleaseTimeRecorder:
    """Story A8: checks NSE's archive itself (never Drive) for a session's participant-OI file and logs each check."""
    return ReleaseTimeRecorder(
        build_nse_source(ParticipantOiSource),
        ParticipantOiSource.path_for,
        load_session_calendar(CALENDAR_FILE),
        ReleaseLog(PARTICIPANT_OI_RELEASE_LOG),
    )


def build_participant_oi_rule() -> AvailabilityRule:
    """When a decision may use a day's participant-OI file: set from the committed release-time evidence."""
    checks = ReleaseLog(PARTICIPANT_OI_RELEASE_LOG).checks()
    return choose_availability_rule(checks, load_session_calendar(CALENDAR_FILE), DESK_DECISION_TIME)


def build_point_in_time_participant_oi(project_folder: Path | None = None) -> PointInTimeParticipantOi:
    """Participant OI as a decision at a given moment could have known it (story A8)."""
    library = build_participant_oi_library(project_folder)
    return PointInTimeParticipantOi(
        lambda day: library.get(ParticipantOiSource.path_for(day)).data,
        ParticipantOiSource.filename_for,
        load_session_calendar(CALENDAR_FILE),
        build_participant_oi_rule(),
    )
