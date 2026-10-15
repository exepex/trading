"""Composition root of the study: Drive, A12's archive, the cache and the repository's files become `analysis.Inputs`.

Reads only Drive and the repository (the owner's one-downloader rule). Its only writes are A12's own board-meeting
fill (`fill_results_dates`, through A12's librarian) and the study's outputs. No order code, no Groww call.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import date, timedelta
from pathlib import Path

from fno.config import load_config
from fno.constants import FILING_BOARD_MEETINGS
from fno.filings.sources import NseBoardMeetingsSource
from fno.filings.wiring import build_day_list_librarian
from fno.fo_bhavcopy import read_index_closes
from fno.storage.librarian import FillReport, fill_report_lines
from fno.storage.raw_source import NseDailyFoSource, NseIndexCloseSource, NseLegacyFoSource
from fno.storage.wiring import build_drive_reader, build_session_calendar

from .analysis import Inputs
from .events import Meeting
from .inputs import REPOSITORY, DatasetFiles, InputCache, checked, manifest_rows
from .sessions import Sessions
from .sources import corporate_actions, read_filing_times, read_meetings, read_sectors, symbol_names
from .spreads import QuotedLeg

FOLDER = Path(__file__).resolve().parents[1]
UDIFF = DatasetFiles("fo-bhavcopy", NseDailyFoSource.path_for, NseDailyFoSource.filename_for, date(2024, 1, 1))
LEGACY = DatasetFiles(
    "fo-bhavcopy-legacy", NseLegacyFoSource.path_for, NseLegacyFoSource.filename_for, date(2019, 1, 1), date(2024, 7, 5)
)
INDEX_CLOSE = DatasetFiles(
    "index-close", NseIndexCloseSource.path_for, NseIndexCloseSource.filename_for, date(2018, 12, 1)
)
NIFTY_50 = "Nifty 50"
SNAPSHOTS = {  # Drive raw path, manifest name, day
    "sectors": ("nse/indices/nifty500-list/2026/10/12/ind_nifty500list.csv", "nifty500-list", date(2026, 10, 12)),
    "names": ("nse/equities/symbol-change/2026/10/13/symbolchange.csv", "symbol-change", date(2026, 10, 13)),
    "actions": (
        "nse/equities/corporate-actions/2026/10/13/corporate-actions-equities.json",
        "corporate-actions",
        date(2026, 10, 13),
    ),
}
MEETINGS = DatasetFiles(
    FILING_BOARD_MEETINGS, NseBoardMeetingsSource.path_for, NseBoardMeetingsSource.filename_for, date(2018, 12, 1)
)
MEETINGS_FIRST = date(2018, 12, 1)  # the entry session of a 2 Jan 2019 reaction is in late December 2018
FILINGS_MANIFEST = REPOSITORY / "research" / "data" / "manifests" / "filings" / "results-xbrl.csv"
LEDGER = REPOSITORY / "research" / "ledger.csv"
LATER_DAYS = 60  # calendar sessions after the last F&O file, to count sessions up to an expiry (amendment 1 D5)
CALENDAR_END = date(2026, 12, 31)  # research/data/calendar/nse_sessions.csv covers NSE's circulars up to here
FROZEN = ("study.py", "snapshot.py", "AMENDMENT_2.md")  # with every r2study/*.py: hashed in FREEZE.md


def sessions_from_manifests(log=print) -> Sessions:
    """Days with an F&O file; days NSE's calendar does not call sessions (e.g. muhurat) are reported, and kept: NSE
    published a file for them, so contracts traded that day."""
    days = [d for d in set(manifest_rows(UDIFF.name)) | set(manifest_rows(LEGACY.name)) if d >= LEGACY.first]
    calendar = build_session_calendar()
    stray = sorted(d for d in days if not calendar.is_session(d))
    log(f"sessions: {len(days)} days with an F&O file; {len(stray)} not regular sessions in the calendar: {stray}")
    last = max(days)
    later = calendar.sessions(last + timedelta(days=1), min(last + timedelta(days=LATER_DAYS), CALENDAR_END))
    return Sessions(days, later)


def snapshot_bytes(drive, name: str) -> bytes:
    path, manifest, day = SNAPSHOTS[name]
    return checked(drive.get(path), manifest_rows(manifest)[day], path)


def fill_results_dates(last: date, log=print) -> FillReport:
    """A12's board-meeting day lists from 1 Dec 2018 to `last`, through A12's own librarian (one day per request, its
    names, layout, content check and manifest rows; amendment 1 D1). Archiving only: nothing is parsed here."""
    report = build_day_list_librarian(FILING_BOARD_MEETINGS, log=log).fill(MEETINGS_FIRST, last)
    for line in fill_report_lines(report):
        log(line)
    return report


class MissingResultsDates(RuntimeError):
    """A calendar day of the study's range has no archived board-meeting list: the run cannot answer (stage 0)."""


def meetings_from_archive(cache: InputCache, last: date, log=print) -> list[Meeting]:
    """Every results-date row from A12's archived day lists, each file checked against its manifest row; refuses to
    go on if any calendar day of the range is missing (amendment 1 D1's completeness proof)."""
    rows = manifest_rows(MEETINGS.name)
    days = [MEETINGS_FIRST + timedelta(days=i) for i in range((last - MEETINGS_FIRST).days + 1)]
    missing = [d for d in days if d not in rows]
    if missing:
        raise MissingResultsDates(f"{len(missing)} days without an archived board-meeting list, first {missing[:3]}")
    cache.fetch(MEETINGS, log=log)
    meetings, skipped = [], 0
    for day in days:
        found, rows_skipped = read_meetings(cache.read(MEETINGS, day)[1])
        meetings += found
        skipped += rows_skipped
    log(f"board meetings: {len(days)} day lists, {len(meetings)} rows, {skipped} rows without a symbol or date")
    return meetings


def read_snapshot_legs(path: Path) -> list[QuotedLeg]:
    """The snapshot's derived legs file (one JSON object per line, made by snapshot.py)."""
    return [QuotedLeg(**json.loads(line)) for line in path.read_text().splitlines() if line.strip()]


def build_inputs(cache_folder: Path, snapshot: Path | None, workers: int, last: date) -> Inputs:
    drive = build_drive_reader()
    cache = InputCache(cache_folder, drive.get)
    sessions = sessions_from_manifests()
    udiff_days, legacy_days = set(cache.days(UDIFF)), set(cache.days(LEGACY))
    names = symbol_names(snapshot_bytes(drive, "names"))
    meetings = meetings_from_archive(cache, last)
    closes: dict[date, float | None] = {}

    def nifty(day: date) -> float | None:
        if day not in closes:
            found = cache.read(INDEX_CLOSE, day)
            closes[day] = read_index_closes(found[1], found[0]).get(NIFTY_50) if found else None
        return closes[day]

    return Inputs(
        sessions=sessions,
        current=lambda d: cache.read(UDIFF, d) if d in udiff_days else None,
        legacy=lambda d: cache.read(LEGACY, d) if d in legacy_days else None,
        nifty=nifty,
        meetings=meetings,
        filing_times=read_filing_times(FILINGS_MANIFEST),
        sectors=read_sectors(snapshot_bytes(drive, "sectors")),
        names=names,
        actions=corporate_actions(snapshot_bytes(drive, "actions"), names),
        charges=load_config()["charges"],
        snapshot=read_snapshot_legs(snapshot) if snapshot else None,
        workers=workers,
    )


class NotFrozen(RuntimeError):
    """The code about to run is not the code whose hashes FREEZE.md records, or the folder has uncommitted changes."""


def check_frozen() -> None:
    """Refuses the run unless every script file's SHA-256 is in FREEZE.md and git sees no change in the folder."""
    freeze = (FOLDER / "FREEZE.md").read_text()
    files = [FOLDER / name for name in FROZEN] + sorted((FOLDER / "r2study").glob("*.py"))
    unfrozen = [f.name for f in files if hashlib.sha256(f.read_bytes()).hexdigest() not in freeze]
    status = subprocess.run(["git", "status", "--porcelain", "--", str(FOLDER)], capture_output=True, text=True)
    dirty = [line for line in status.stdout.splitlines() if not line.endswith(("results.json", "results.md"))]
    if unfrozen or dirty or status.returncode:
        raise NotFrozen(f"not frozen: {unfrozen}; uncommitted: {dirty}")


def trials_total() -> int:
    with LEDGER.open(newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))
