"""Composition root of the market school's paper record (story MS-P1j): the fleet over the pilot's real stores,
which only this root builds: the dashcam on Drive with receipts pushed to `main`, the accounts and ticket ledger
mirrored to Drive's private area, and the counts committed by this one runner; and g's report inputs. What both the
record and the replay wire alike is `fleet_wiring.fleet_on`; a replay is `replay_wiring.build_replay_fleet`.

`school.enabled` is the only switch."""

from datetime import date, datetime
from pathlib import Path

from ..composition import build_alert_sender
from ..config import ROOT
from ..models import now_ist
from ..storage.wiring import QUOTES_FOLDER
from .accounts.wiring import build_account_sync
from .constants import SCHOOL_OFF_LINE
from .contracts.fleet import RunMode, SessionRun
from .dashcam.names import COUNTS_FOLDER
from .dashcam.wiring import build_dashcam
from .drivers.wiring import build_school_drivers
from .fleet.counts_commit import SessionFilesCommitter
from .fleet.history import RecordedSpotHistory
from .fleet.report_inputs import PreviousSlotToday, SealedDayInputs
from .fleet.runner import SchoolFleet
from .fleet.session_hook import IsolatedSessionStep
from .fleet.unfilled import UnfilledEntries
from .fleet_wiring import FleetStores, fleet_on
from .instructor.outputs.public_counts import counts_path as instructor_counts_path
from .instructor.wiring import build_why_lines, run_instructor_session
from .quality.wiring import build_quality_gate
from .roads.wiring import build_road_services
from .settings import school_settings

COUNTS_MESSAGE = "Counts: school session counts ({what})"
INSTRUCTOR = "instructor"


class IstClock:
    def now(self) -> datetime:
        return now_ist()


class SwitchedOff:
    """The pilot with `school.enabled` off: the school-off line, with nothing built, read or written."""

    def run(self, session: date, mode: RunMode) -> SessionRun:
        return SessionRun(session, mode, SCHOOL_OFF_LINE)


def build_fleet(cfg: dict, root: Path = ROOT) -> SchoolFleet | SwitchedOff:
    """The paper record's fleet over the pilot's real stores, or the switched-off runner: `school.enabled` is read
    here, at the pilot's entry, never by the fleet (a replay is `replay_wiring.build_replay_fleet`, which has none)."""
    if not school_settings(cfg).enabled:
        return SwitchedOff()
    committer = SessionFilesCommitter(Path(root), Path(root) / COUNTS_FOLDER, COUNTS_MESSAGE)
    stores = FleetStores(Path(root), build_dashcam(), committer, build_account_sync(root), IstClock(),
                         lambda session: (str(instructor_counts_path(session)),))  # fmt: skip
    return fleet_on(cfg, stores, root, build_instructor_step(cfg))


def build_instructor_step(cfg: dict) -> IsolatedSessionStep:
    """MS-INS part e's session run, after the outcomes' seal and before the counts' commit, which takes its counts
    file (`research/school/counts/instructor/`); isolated, so it can never stop the school's record."""
    return IsolatedSessionStep(INSTRUCTOR, lambda session: run_instructor_session(cfg, session, write=True),
                               build_alert_sender().send)  # fmt: skip


def build_report_inputs(cfg: dict, root: Path = ROOT) -> tuple[PreviousSlotToday, SealedDayInputs]:
    """g's two ports: the 08:50 plan from the previous slot, and the 20:05 day from the sealed record and counts."""
    services = build_road_services()
    drivers = build_school_drivers(cfg, root)
    gate, history = build_quality_gate(services.listing), RecordedSpotHistory(QUOTES_FOLDER)
    today = PreviousSlotToday(services.calendar, services.catalogue, services.snapshots, gate, drivers, history)
    roles = {driver.card.driver_id: driver.card.role for driver in drivers}
    return today, SealedDayInputs(build_dashcam(), root, roles, build_why_lines(cfg))


def build_unfilled_entries(cfg: dict, root: Path = ROOT) -> UnfilledEntries:
    """MS-INS part e's `unfilled`: the record's fired entries that never filled, over the record's own stores."""
    fleet = build_fleet(cfg, root)
    return UnfilledEntries(fleet.dashcam, fleet.books.account_entries, fleet.books.ticket_entries)
