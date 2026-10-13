"""Composition root of the F&O app: the only place that picks concrete classes for the app's services (raw data stores
and sources are wired in `fno/storage/wiring.py`). Swapping a provider or store changes this file only."""

from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from datetime import date, datetime, time
from pathlib import Path

import numpy

from .alerts.sender import AlertSender, NoAlertSender, SlackChannelAlerts
from .books.account import AccountWriter, PaperAccount
from .books.lock import DEFAULT_LEASE_SECONDS, AccountLock
from .config import ROOT
from .constants import ENV_FNO_SLACK_BOT_TOKEN, FNO_DESK_CHANNEL_ID, NIFTY_SYMBOL
from .providers import AUTO_PROVIDER, get_provider
from .quotes.expiry_listing import NseDailyFileExpiries
from .quotes.recorder import QuoteSnapshotRecorder
from .record_scan.catalogue import ALLOWED_VALUES, credential_patterns, record_patterns
from .record_scan.scanner import RecordScanner
from .research_data.availability import AvailabilityRule, LastWriteBoundRule
from .research_data.events import read_events
from .research_data.last_written import latest_writes, read_last_modified_table
from .research_data.panel_reader import NiftyPanel, read_nifty_panel
from .research_data.positioning import PointInTimeParticipantOi
from .research_data.release_times import ReleaseLog, ReleaseTimeRecorder, choose_availability_rule, last_written_times
from .research_data.write_sweep import LastWriteSweep, read_sweeps
from .research_engine.cycle_costs import CycleTerms
from .research_engine.cycles import Cycle, cycle_rows, monthly_cycles
from .research_engine.event_features import ScheduledEventInWindow
from .research_engine.experiments import Period
from .research_engine.features import Feature, ResearchData
from .research_engine.implied_vol import Black76
from .research_engine.ledger import Ledger
from .research_engine.runner import ExperimentRunner
from .research_engine.simulator import CycleSimulator
from .research_engine.structures import LongIronFly, ShortCondor, ShortIronFly, Structure
from .research_engine.trial_guard import LedgerTrialGuard
from .research_engine.volatility_features import AtmIvMinusRealised, VixAboveMedian
from .storage.raw_source import ParticipantOiSource
from .storage.wiring import (
    CALENDAR_FILE,
    EVENTS_FILE,
    PANEL_FOLDER,
    PARTICIPANT_OI_LAST_MODIFIED,
    PARTICIPANT_OI_RELEASE_LOG,
    PARTICIPANT_OI_SWEEPS,
    build_nse_fo_library,
    build_nse_source,
    build_participant_oi_library,
    build_quote_store,
    build_session_calendar,
)

DESK_DECISION_TIME = time(15, 0)  # design 13.5: books decide at about 15:00 IST; story E3 freezes the exact timetable


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


def build_release_time_recorder() -> ReleaseTimeRecorder:
    """Story A8: checks NSE's archive itself (never Drive) for a session's participant-OI file and logs each check."""
    return ReleaseTimeRecorder(
        build_nse_source(ParticipantOiSource),
        ParticipantOiSource.path_for,
        build_session_calendar(),
        ReleaseLog(PARTICIPANT_OI_RELEASE_LOG),
    )


def build_participant_oi_rule() -> AvailabilityRule:
    """When a decision may use a day's participant-OI file: set from the committed release-time evidence, and never
    before the bytes held were last written (judge 15: NSE rewrote 105 of 1,929 files after publishing them)."""
    checks, calendar = ReleaseLog(PARTICIPANT_OI_RELEASE_LOG).checks(), build_session_calendar()
    rule = choose_availability_rule(checks, calendar, DESK_DECISION_TIME)
    return LastWriteBoundRule(rule, calendar, DESK_DECISION_TIME, participant_oi_last_writes())


def participant_oi_last_writes() -> dict[date, datetime]:
    """Day -> the latest write time NSE reported for its participant-OI file, from every committed record."""
    checks = ReleaseLog(PARTICIPANT_OI_RELEASE_LOG).checks()
    table = read_last_modified_table(PARTICIPANT_OI_LAST_MODIFIED)
    return latest_writes(table, last_written_times(checks), read_sweeps(PARTICIPANT_OI_SWEEPS))


def build_last_write_sweep() -> LastWriteSweep:
    """Judge 16: a headers-only pass over every recorded participant-OI file, straight to NSE (never Drive)."""
    return LastWriteSweep(build_nse_source(ParticipantOiSource), ParticipantOiSource.path_for, PARTICIPANT_OI_SWEEPS)


def build_point_in_time_participant_oi(project_folder: Path | None = None) -> PointInTimeParticipantOi:
    """Participant OI as a decision at a given moment could have known it (story A8)."""
    library = build_participant_oi_library(project_folder)
    return PointInTimeParticipantOi(
        lambda day: library.get(ParticipantOiSource.path_for(day)).data,
        ParticipantOiSource.filename_for,
        build_session_calendar(),
        build_participant_oi_rule(),
    )


def build_features(cfg: dict) -> tuple[Feature, ...]:
    """Experiment 1's daily-close features (story B1). F1 prices on the same-expiry future with Black-76 (story B1 note
    of 13 Oct 2026); the `risk_free_rate` setting only discounts."""
    return (AtmIvMinusRealised(Black76(), cfg["risk_free_rate"]), VixAboveMedian(), ScheduledEventInWindow())


def load_research_data(years=None, keep=None) -> ResearchData:
    """The repository's NIFTY panel (story A3; `years` and `keep` as in `read_nifty_panel`) and events calendar (A6)."""
    return ResearchData(read_nifty_panel(PANEL_FOLDER, years, keep), tuple(read_events(EVENTS_FILE.read_text())))


def build_cycles(panel: NiftyPanel) -> list[Cycle]:
    """Experiment 1's monthly cycles of the panel (story B2): A5's monthly rule and NSE's session calendar (A1)."""
    return monthly_cycles(panel, build_session_calendar())


def build_structures() -> tuple[Structure, ...]:
    """Experiment 1's structures SF, SC and BF (story B2)."""
    return ShortIronFly(), ShortCondor(), LongIronFly()


def build_cycle_simulator(cfg: dict, panel: NiftyPanel) -> CycleSimulator:
    """Story B2's simulator: one NIFTY lot (`lot_sizes`) and the `charges` block of config.yaml; the protocol's pad,
    loss cap and widths."""
    return CycleSimulator(panel, CycleTerms(lot=cfg["lot_sizes"][NIFTY_SYMBOL], charges=cfg["charges"]))


def load_period_data(period: Period) -> ResearchData:
    """A period's research data (story B3): option rows only from the period's first decision day on (and only those
    cycles use, 21+ days to expiry), so an earlier period's option outcomes are never held; index closes from the year
    before, for the features' look-back (F1: 21 closes, F2: 250); option rows a year after the end, for late exits."""
    years = range(period.start.year - 1, period.end.year + 2)
    return load_research_data(years, keep=lambda day, expiry: day >= period.start and cycle_rows(day, expiry))


def research_inputs(cfg: dict) -> dict:
    """SHA-256 of every input a results file depends on, and the numpy version (its generator streams)."""

    files = {"panel_manifest": PANEL_FOLDER / "manifest.json", "events": EVENTS_FILE, "session_calendar": CALENDAR_FILE}
    terms = {key: cfg[key] for key in ("charges", "lot_sizes", "risk_free_rate")}
    return {
        **{name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()},
        "config_terms": hashlib.sha256(json.dumps(terms, sort_keys=True).encode()).hexdigest(),
        "numpy": numpy.__version__,
    }


def build_ledger(root: Path = ROOT) -> Ledger:
    return Ledger(root)


def build_experiment_runner(cfg: dict, root: Path = ROOT) -> ExperimentRunner:
    """Story B3's runner: B4's ledger guard, the repository's panel and events, B1's features, B2's cycles,
    structures and simulator."""
    ledger = build_ledger(root)
    return ExperimentRunner(
        guard=LedgerTrialGuard(ledger),
        load_data=load_period_data,
        build_cycles=build_cycles,
        features=build_features(cfg),
        structures=build_structures(),
        build_simulator=lambda panel: build_cycle_simulator(cfg, panel),
        ledger_count=ledger.count,
        inputs=lambda: research_inputs(cfg),
    )
