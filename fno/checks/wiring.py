"""Composition root of the data checks (story C3): the checks in the order they report, the quote store the snapshot
is read from, the shock flag source, the NSE file stores and the alert sender. Also of the hard-validity checks (story
C4): the evidence store, the charge table and owner limits from config.yaml, each book's mode, the failure log. Swapping
any changes this file only."""

from __future__ import annotations

from pathlib import Path

from .data_checks import DataChecks
from .gate import DataGate
from .leg_checks import LegQuotesValid
from .market_checks import PreviousSessionFile, SpotNearPreviousClose
from .schedule import ExecutionSchedule, PackSnapshotSchedule
from .shock import NoShockFlags
from .snapshot_checks import SnapshotInWindow, SnapshotMatchesRecord, SnapshotReadable
from .validity import Sources, ValidityChecker
from .validity_account import LedgerAccounts
from .validity_adapter import BookTradeValidator, CaptureSource
from .validity_evidence import EvidenceReader
from .validity_limits import LimitChecks
from .validity_listing import NseListing
from .validity_margin import MarginFile
from .validity_modes import PlaybookMode, ValidityMode, WaitsFor
from .validity_settings import limits_from_config


def build_data_checks(stores, calendar, shocks=None) -> DataChecks:
    from ..storage.raw_source import NseDailyFoSource

    return DataChecks(
        (
            SnapshotReadable(),
            SnapshotInWindow(),
            SnapshotMatchesRecord(),
            SpotNearPreviousClose(calendar, shocks or NoShockFlags()),
            LegQuotesValid(),
            PreviousSessionFile(stores, NseDailyFoSource, calendar),
        )
    )


def build_data_gate(quote_folder: Path | None = None, schedule: ExecutionSchedule | None = None) -> DataGate:
    """The gate the desk runs before each decision; E3 passes its own execution schedule."""
    from ..composition import build_alert_sender, build_session_calendar
    from ..desk.wiring import build_execution_snapshots
    from ..storage.wiring import build_raw_stores

    checks = build_data_checks(build_raw_stores(), build_session_calendar())
    snapshots = build_execution_snapshots(quote_folder)
    return DataGate(checks, snapshots, schedule or PackSnapshotSchedule(), build_alert_sender())


def validity_modes() -> dict[str, ValidityMode]:
    """Book 1 checks against the playbook; books 2 and 3 fail closed until D4's envelope and D5's constitution exist."""
    from ..constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI

    return {
        BOOK1_RULES: PlaybookMode(),
        BOOK2_HYBRID: WaitsFor("envelope", "D4"),
        BOOK3_AI: WaitsFor("constitution", "D5"),
    }


def build_validity_checker(cfg: dict, root: Path, quotes, nse_library, accounts=None, margins=None) -> ValidityChecker:
    """C4's checker: the A4 quote store, NSE's F&O files (A2's library), the books' ledgers and A14's margins file;
    charges and the books' risk profile read straight from config.yaml, never through C2 or B2."""
    from ..constants import RISK_PROFILE_BOOKS
    from ..quotes.recorder import DATASET
    from ..storage.wiring import build_session_calendar

    limits = limits_from_config(cfg, root, RISK_PROFILE_BOOKS, build_session_calendar().previous_session)
    sources = Sources(EvidenceReader(quotes, DATASET), NseListing(nse_library), accounts or LedgerAccounts(root))
    checks = LimitChecks(limits, cfg["charges"], margins or MarginFile(limits.margins.file))
    return ValidityChecker(sources, checks, validity_modes())


def build_trade_validator(
    cfg: dict, book: str, root: Path, captures: CaptureSource | None = None, log: bool = True,
    quote_folder: Path | None = None,
) -> BookTradeValidator:  # fmt: skip
    """The validator D3's decision run calls for `book`; a replay passes `log=False` so it writes nothing."""
    from ..composition import DESK_DECISION_TIME
    from ..desk.pack_store import PackStore
    from ..storage.wiring import build_nse_fo_library, build_quote_store
    from .validity_capture import PackCaptures
    from .validity_failures import ValidityFailureLog

    checker = build_validity_checker(cfg, root, build_quote_store(quote_folder), build_nse_fo_library())
    captures = captures or PackCaptures(PackStore(root), PackSnapshotSchedule())
    return BookTradeValidator(book, checker, captures, DESK_DECISION_TIME, ValidityFailureLog(root) if log else None)
