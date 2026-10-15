"""Composition root of story A17, the global cues: the only place that picks the concrete sources (Cboe, Nasdaq,
US Treasury, EIA, RBI, FBIL), the shared polite HTTP session, the owner's Drive raw area, the snapshot logs, the tables
in the repository (public cues) or Drive's derived area (private cues: the S&P 500 and Nasdaq 100, owner decision
a927390) and NSE's session calendar for the `live` rule. Swapping a source is one line in SOURCES."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import date, timedelta

from ..constants import DERIVED_AREA, RESEARCH_USER_AGENT
from ..http_pacing import PacedSession
from ..models import now_ist
from ..research_data.calendar import SessionCalendar
from ..storage import wiring as storage
from ..storage.raw_store import AreaStore, RawFileStore
from .check_files import CueChecks
from .collector import CueCollector
from .job import GlobalCueJob
from .other_sources import EiaBrentSource, FbilUsdInrSource, RbiUsdInrSource
from .row_log import CsvRowLog, DrivePartsRowLog, DriveSnapshots
from .snapshot_log import SnapshotLog
from .source import GlobalCueSource
from .table import CueTable
from .treasury_source import TreasuryTenYearSource
from .us_index_sources import CboeSp500Source, NasdaqNdxSource
from .verify import CueTableVerifier

CUES_FOLDER = storage.REPOSITORY / "research" / "data" / "global-cues"
CHECKS_FOLDER = CUES_FOLDER / "checks"
SNAPSHOT_LOG_FOLDER = storage.MANIFEST_FOLDER / "global-cues"  # one row per archived copy, like the manifests
REVISIONS_FILE = "revisions.csv"  # the public cues' shared revision log
PRIVATE_FOLDER = "global-cues"  # in Drive's derived area: <cue>/rows, <cue>/revisions, <cue>/checks
SOURCES: tuple[GlobalCueSource, ...] = (
    CboeSp500Source(),
    NasdaqNdxSource(),
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


def _after() -> Callable[[date], date]:
    calendar = storage.build_session_calendar()
    return next_nse_session(calendar, calendar.first)


def _owner_drive(env=os.environ):
    drive = storage.build_owner_drive(env)
    if drive is None:
        raise RuntimeError(DRIVE_SETTINGS_MISSING)
    return drive


def _private_log(env, cue: str, kind: str) -> DrivePartsRowLog:
    """A private cue's rows, revisions or gaps: write-once parts in Drive's derived area (owner decision a927390)."""
    return DrivePartsRowLog(AreaStore(_owner_drive(env), DERIVED_AREA), f"{PRIVATE_FOLDER}/{cue}/{kind}", now_ist)


def build_tables(include_private: bool = True, env=os.environ) -> dict[str, CueTable]:
    """Public cues' tables in the repository; private cues' in Drive (needs the Drive settings)."""
    after, shared_revisions = _after(), CsvRowLog(CUES_FOLDER / REVISIONS_FILE)
    tables = {
        s.cue: CueTable(s.cue, CsvRowLog(CUES_FOLDER / f"{s.cue}.csv"), shared_revisions, after)
        for s in SOURCES
        if not s.private
    }
    for s in SOURCES if include_private else ():
        if s.private:
            tables[s.cue] = CueTable(
                s.cue, _private_log(env, s.cue, "rows"), _private_log(env, s.cue, "revisions"), after
            )
    return tables


def _checks(tables: dict[str, CueTable], env=os.environ) -> CueChecks:
    private = {
        s.cue: DriveSnapshots(AreaStore(_owner_drive(env), DERIVED_AREA), f"{PRIVATE_FOLDER}/{s.cue}/checks", now_ist)
        for s in SOURCES
        if s.private and s.cue in tables
    }
    return CueChecks(tables, CHECKS_FOLDER, private)


def build_raw_area(env=os.environ) -> RawFileStore:
    return AreaStore(_owner_drive(env), storage.RAW_AREA)


def build_job(env=os.environ) -> GlobalCueJob:
    session = PacedSession()
    session.headers["User-Agent"] = RESEARCH_USER_AGENT
    collector = CueCollector(session, build_raw_area(env), SnapshotLog(SNAPSHOT_LOG_FOLDER), now_ist)
    tables = build_tables(env=env)
    return GlobalCueJob(collector, tables, _checks(tables, env))


def build_checks(env=os.environ) -> CueChecks:
    """The checks from the tables: public ones only when the Drive settings are missing (no network otherwise)."""
    with_drive = storage.build_owner_drive(env) is not None
    tables = build_tables(include_private=with_drive, env=env)
    return _checks(tables, env)


def build_verifier(env=os.environ) -> CueTableVerifier:
    return CueTableVerifier(build_raw_area(env), SnapshotLog(SNAPSHOT_LOG_FOLDER), _after())
