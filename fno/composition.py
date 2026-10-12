"""Composition root of the F&O app: the only place that picks concrete classes for the app's services (raw data stores
and sources are wired in `fno/storage/wiring.py`). Swapping a provider or store changes this file only."""

from __future__ import annotations

import os
from contextlib import contextmanager
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
from .storage.wiring import build_nse_fo_library, build_quote_store, build_session_calendar


def build_quote_recorder(cfg: dict) -> QuoteSnapshotRecorder:
    """The 3 pm quote recorder (story A4): its own `quotes.provider` setting (`auto`: Groww when its credentials are
    set, else NSE), never the root `provider` used by the `chain` command; the repository quote store; NSE's daily
    files, for expiry dates the provider cannot list and to prove which expiries are monthly (A5's point-in-time rule);
    and NSE's session calendar, which decides whether today is a session (A7)."""
    provider = get_provider(cfg.get("quotes", {}).get("provider", AUTO_PROVIDER), cfg)
    expiries = NseDailyFileExpiries(build_nse_fo_library())
    return QuoteSnapshotRecorder(
        provider, build_quote_store(), fallback=expiries, calendar=build_session_calendar(), history=expiries
    )


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
