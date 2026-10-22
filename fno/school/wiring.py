"""Composition root of the market school (story MS-P1j): the fleet runner over b's roads and quality gate, the drivers
of e, d's laws, accounts and fills, f's ticket book, c's dashcam and the run's counts, and g's report inputs.

`school.enabled` is the only switch. `RunMode.RECORD` is the paper record: accounts and tickets mirrored to Drive's
private area, the dashcam on Drive with receipts pushed to `main`, the counts committed by this one runner.
`RunMode.REPLAY` is a recorded session again in a local folder: no Drive write, no push, no commit, a fixed clock;
the captures, archived NSE files and margin file are still read from where they are stored (read-only)."""

from datetime import date, datetime, time
from pathlib import Path

from ..config import ROOT
from ..models import IST, now_ist
from ..storage.manifest_commit import GitManifestRecorder
from ..storage.wiring import QUOTES_FOLDER
from .accounts.names import school_root
from .accounts.reviews import REVIEWS_FILE, ReviewFile
from .accounts.school_accounts import SchoolAccounts
from .accounts.wiring import build_account_port, build_account_sync
from .contracts.clock import Clock, FixedClock
from .contracts.fleet import RunMode
from .dashcam.names import COUNTS_FOLDER
from .dashcam.wiring import build_dashcam
from .drivers.wiring import build_school_drivers
from .execution.wiring import build_capture_1515, build_fill_port
from .fleet.books import Books
from .fleet.counts_file import SessionCounts
from .fleet.entry_mids import DashcamEntryMids
from .fleet.history import RecordedSpotHistory
from .fleet.replay_store import ReplayDashcam
from .fleet.report_inputs import PreviousSlotToday, SealedDayInputs
from .fleet.runner import SchoolFleet
from .quality.wiring import build_quality_gate
from .roads.wiring import build_road_services
from .safety.wiring import build_margin, build_safety_laws
from .settings import school_settings
from .tickets.book import TicketBook, TicketLedger

TICKETS_FOLDER = "tickets"  # journal/school/tickets: the ticket ledger, apart from every driver account
REPLAY_FILL_TIME = time(15, 20)  # a replay's fixed clock: after every road's capture window, as the run would be
COUNTS_MESSAGE = "Counts: school session counts ({what})"


class IstClock:
    def now(self) -> datetime:
        return now_ist()


def replay_clock(session: date) -> FixedClock:
    return FixedClock(datetime.combine(session, REPLAY_FILL_TIME, tzinfo=IST))


def build_fleet(cfg: dict, mode: RunMode, session: date, root: Path = ROOT, replay_folder: Path | None = None
                ) -> SchoolFleet:  # fmt: skip
    """`replay_folder` is required in replay: every write of the run goes under it."""
    settings = school_settings(cfg)
    replay = mode is RunMode.REPLAY
    if replay and replay_folder is None:
        raise ValueError("a replay writes only under its own folder")
    clock: Clock = replay_clock(session) if replay else IstClock()
    home = Path(replay_folder) if replay else Path(root)
    sync = None if replay else build_account_sync(root)
    accounts = build_account_port(cfg, settings, home, sync)
    tickets_accounts = SchoolAccounts(school_root(home) / TICKETS_FOLDER, settings.account_rs, settings.brake_rs,
                                      cfg["charges"], ReviewFile(Path(root) / REVIEWS_FILE), sync)  # fmt: skip
    fills = build_fill_port(cfg)
    books = Books(accounts, accounts, TicketBook(fills, TicketLedger(tickets_accounts)), tickets_accounts, fills)
    dashcam = ReplayDashcam(home / "dashcam", clock) if replay else build_dashcam()
    committer = None if replay else GitManifestRecorder(Path(root), Path(root) / COUNTS_FOLDER, message=COUNTS_MESSAGE)
    services = build_road_services()
    margin = build_margin(cfg)
    capture = build_capture_1515(root)
    return SchoolFleet(
        settings, services.catalogue, services.snapshots, build_quality_gate(services.listing),
        RecordedSpotHistory(QUOTES_FOLDER), build_school_drivers(cfg, root),
        lambda marks: build_safety_laws(cfg, settings, marks, margin), books, dashcam, SessionCounts(home, committer),
        capture.for_session, DashcamEntryMids(dashcam), clock,
    )  # fmt: skip


def build_report_inputs(cfg: dict, root: Path = ROOT) -> tuple[PreviousSlotToday, SealedDayInputs]:
    """g's two ports: the 08:50 plan from the previous slot, and the 20:05 day from the sealed record and counts."""
    services = build_road_services()
    drivers = build_school_drivers(cfg, root)
    gate, history = build_quality_gate(services.listing), RecordedSpotHistory(QUOTES_FOLDER)
    today = PreviousSlotToday(services.calendar, services.catalogue, services.snapshots, gate, drivers, history)
    roles = {driver.card.driver_id: driver.card.role for driver in drivers}
    return today, SealedDayInputs(build_dashcam(), root, roles)
