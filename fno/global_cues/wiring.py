"""Composition root of story A17, the global cues: the only place that picks the concrete sources (US Treasury, EIA,
RBI, FBIL), the shared polite HTTP session, the owner's Drive raw area, the snapshot logs, the tables
in the repository and NSE's session calendar for the `live` rule. Swapping a source is one line in SOURCES."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import date, timedelta

from ..constants import RESEARCH_USER_AGENT
from ..http_pacing import PacedSession
from ..models import now_ist
from ..research_data.calendar import SessionCalendar
from ..storage import wiring as storage
from ..storage.raw_store import AreaStore, RawFileStore
from .collector import CueCollector
from .job import CueChecks, GlobalCueJob
from .other_sources import EiaBrentSource, FbilUsdInrSource, RbiUsdInrSource
from .snapshot_log import SnapshotLog
from .source import GlobalCueSource
from .table import CueTable
from .treasury_source import TreasuryTenYearSource
from .verify import CueTableVerifier

CUES_FOLDER = storage.REPOSITORY / "research" / "data" / "global-cues"
CHECKS_FOLDER = CUES_FOLDER / "checks"
SNAPSHOT_LOG_FOLDER = storage.MANIFEST_FOLDER / "global-cues"  # one row per archived copy, like the manifests
SOURCES: tuple[GlobalCueSource, ...] = (
    TreasuryTenYearSource(),
    EiaBrentSource(),
    RbiUsdInrSource(),
    FbilUsdInrSource(),
)
DRIVE_SETTINGS_MISSING = f"set {', '.join(storage.OWNER_UPLOAD_SETTINGS)} to archive the global cues in Drive"


def sources_named(names: list[str] | None) -> list[GlobalCueSource]:
    return [s for s in SOURCES if not names or s.cue in names]


def next_nse_session(calendar: SessionCalendar, first: date) -> Callable[[date], date]:
    """The first NSE session after a date. Before the calendar's first day (`first`, 2017) it is the next day: those
    rows were fetched years later and are `backfilled` either way. After its last year it raises CalendarError, so a
    run stops and names the missing year (add NSE's holiday circular) instead of guessing a label."""

    def after(day: date) -> date:
        if day < first:
            return day + timedelta(days=1)
        return calendar.next_session(day)

    return after


def build_tables() -> dict[str, CueTable]:
    calendar = storage.build_session_calendar()
    after = next_nse_session(calendar, calendar.first)
    return {s.cue: CueTable(CUES_FOLDER, s.cue, after) for s in SOURCES}


def build_raw_area(env=os.environ) -> RawFileStore:
    drive = storage.build_owner_drive(env)
    if drive is None:
        raise RuntimeError(DRIVE_SETTINGS_MISSING)
    return AreaStore(drive, storage.RAW_AREA)


def build_job(env=os.environ) -> GlobalCueJob:
    session = PacedSession()
    session.headers["User-Agent"] = RESEARCH_USER_AGENT
    collector = CueCollector(session, build_raw_area(env), SnapshotLog(SNAPSHOT_LOG_FOLDER), now_ist)
    tables = build_tables()
    return GlobalCueJob(collector, tables, CueChecks(tables, CHECKS_FOLDER))


def build_checks() -> CueChecks:
    """The checks from the committed tables (no network, no Drive)."""
    return CueChecks(build_tables(), CHECKS_FOLDER)


def build_verifier(env=os.environ) -> CueTableVerifier:
    calendar = storage.build_session_calendar()
    after = next_nse_session(calendar, calendar.first)
    return CueTableVerifier(build_raw_area(env), SnapshotLog(SNAPSHOT_LOG_FOLDER), after)
