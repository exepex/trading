"""Composition root of the F&O app: the only place that picks concrete classes for the app's services (raw data stores
and sources are wired in `fno/storage/wiring.py`). Swapping a provider or store changes this file only."""

from __future__ import annotations

from .providers import AUTO_PROVIDER, get_provider
from .quotes.expiry_listing import NseDailyFileExpiries
from .quotes.recorder import QuoteSnapshotRecorder
from .storage.wiring import build_nse_fo_library, build_quote_store


def build_quote_recorder(cfg: dict) -> QuoteSnapshotRecorder:
    """The 3 pm quote recorder (story A4): its own `quotes.provider` setting (`auto`: Groww when its credentials are
    set, else NSE), never the root `provider` used by the `chain` command; the repository quote store; and NSE's daily
    file for expiry dates the provider cannot list."""
    provider = get_provider(cfg.get("quotes", {}).get("provider", AUTO_PROVIDER), cfg)
    return QuoteSnapshotRecorder(provider, build_quote_store(), fallback=NseDailyFileExpiries(build_nse_fo_library()))
