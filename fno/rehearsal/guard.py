"""The rehearsal's guard (story REH1, acceptance 1-4b): before the first step, every outside service is built through
the real composition roots with the mode set, and each must be its rehearsal form. Any problem stops the rehearsal
before anything is written. A planted break of each check is caught by its test."""

from __future__ import annotations

from collections.abc import Callable

from .alert_label import LabelledAlerts
from .card_label import LabelledCardPoster
from .drive import DryrunDrive
from .http_guard import allowed
from .report_label import LabelledReportPoster

LIVE_PROBES = ("https://www.nseindia.com/api/option-chain-indices", "https://api.groww.in/v1/live-data/quote",
               "https://api.anthropic.com/v1/messages", "https://api.github.com/repos/x/y/dispatches",
               "https://query1.finance.yahoo.com/v8/finance/chart/x")  # fmt: skip
NOT_REHEARSED = "rehearsal guard: {what} is {found}, not its rehearsal form"
LIVE_ALLOWED = "rehearsal guard: a live call would be allowed: {url}"


def builders() -> dict[str, tuple[Callable[[], object], tuple[type, ...]]]:
    """Each outside service's real builder and the rehearsal forms it must return (None: no service set up here)."""
    from ..cards.wiring import build_card_poster
    from ..composition import build_alert_sender
    from ..forecast_lab.wiring import build_forecast_poster
    from ..storage.wiring import build_owner_drive

    return {
        "the owner's Drive": (build_owner_drive, (DryrunDrive, type(None))),
        "the #fno-desk alerts": (build_alert_sender, (LabelledAlerts,)),
        "the card's poster": (build_card_poster, (LabelledCardPoster,)),
        "the lab's poster": (build_forecast_poster, (LabelledReportPoster,)),
    }


def problems(services=None, probes=LIVE_PROBES, is_allowed=allowed) -> list[str]:
    found = []
    for what, (build, forms) in (services or builders()).items():
        built = build()
        if not isinstance(built, forms):
            found.append(NOT_REHEARSED.format(what=what, found=type(built).__name__))
    found += [LIVE_ALLOWED.format(url=url) for url in probes if is_allowed("GET", url)]
    return found
