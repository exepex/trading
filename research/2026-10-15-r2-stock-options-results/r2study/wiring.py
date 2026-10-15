"""Composition root of the study: Drive, NSE, the cache and the repository's files become `analysis.Inputs`.

Read-only everywhere except two writes: NSE's board-meeting lists (raw, to Drive's `raw` area and the local cache)
and the study's own outputs. No order code, no Groww call (the snapshot is `snapshot.py`).
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from pathlib import Path

import requests

from fno.config import load_config
from fno.constants import RESEARCH_USER_AGENT
from fno.fo_bhavcopy import read_index_closes
from fno.storage.raw_source import NseDailyFoSource, NseIndexCloseSource, NseLegacyFoSource
from fno.storage.raw_store import AreaStore
from fno.storage.wiring import RAW_AREA, build_drive_reader, build_owner_drive, build_session_calendar

from .analysis import Inputs
from .inputs import REPOSITORY, DatasetFiles, InputCache, checked, manifest_rows
from .sessions import Sessions
from .sources import (
    BOARD_MEETINGS_API,
    corporate_actions,
    months,
    read_filing_times,
    read_meetings,
    read_sectors,
    symbol_names,
)
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
MEETINGS_DATASET = "nse/equities/filings/board-meetings-by-month"
MEETINGS_FIRST = date(2018, 12, 1)  # the entry session of a 2 Jan 2019 reaction is in late December 2018
INPUTS_FILE = FOLDER / "inputs.csv"
FILINGS_MANIFEST = REPOSITORY / "research" / "data" / "manifests" / "filings" / "results-xbrl.csv"
LEDGER = REPOSITORY / "research" / "ledger.csv"


def sessions_from_manifests(log=print) -> Sessions:
    """Days with an F&O file; days NSE's calendar does not call sessions (e.g. muhurat) are reported, and kept: NSE
    published a file for them, so contracts traded that day."""
    days = [d for d in set(manifest_rows(UDIFF.name)) | set(manifest_rows(LEGACY.name)) if d >= LEGACY.first]
    calendar = build_session_calendar()
    stray = sorted(d for d in days if not calendar.is_session(d))
    log(f"sessions: {len(days)} days with an F&O file; {len(stray)} not regular sessions in the calendar: {stray}")
    return Sessions(days)


def snapshot_bytes(drive, name: str) -> bytes:
    path, manifest, day = SNAPSHOTS[name]
    return checked(drive.get(path), manifest_rows(manifest)[day], path)


def meetings_path(start: date, end: date) -> str:
    return f"{MEETINGS_DATASET}/{start:%Y/%m}/board-meetings_{start:%Y%m%d}_{end:%Y%m%d}.json"


def fetch_meetings(cache: Path, last: date, log=print) -> list[tuple[str, bytes]]:
    """NSE's board-meeting list, one request per calendar month; kept in the cache and, once, in Drive's raw area."""
    session = requests.Session()
    session.headers.update({"User-Agent": RESEARCH_USER_AGENT, "Referer": "https://www.nseindia.com/"})
    owner = build_owner_drive()
    store = AreaStore(owner, RAW_AREA) if owner is not None else None
    out = []
    for start, end in months(MEETINGS_FIRST, last):
        path = meetings_path(start, end)
        local = cache / path
        if not local.exists():
            response = session.get(BOARD_MEETINGS_API.format(start=start, end=end), timeout=60)
            response.raise_for_status()
            if not isinstance(json.loads(response.content), list):
                raise ValueError(f"{path}: NSE did not answer with a list of meetings")
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(response.content)
            if store is not None:
                store.put(path, response.content)
        out.append((path, local.read_bytes()))
    kept = "Drive copy kept" if store else "NOT kept in Drive: no owner sign-in"
    log(f"board meetings: {len(out)} monthly lists ({kept})")
    return out


def write_inputs_record(files: list[tuple[str, bytes]]) -> None:
    with INPUTS_FILE.open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["path", "sha256", "size_bytes"])
        for path, data in files:
            writer.writerow([path, hashlib.sha256(data).hexdigest(), len(data)])


def read_snapshot_legs(path: Path) -> list[QuotedLeg]:
    """The snapshot's derived legs file (one JSON object per line, made by snapshot.py)."""
    return [QuotedLeg(**json.loads(line)) for line in path.read_text().splitlines() if line.strip()]


def build_inputs(cache_folder: Path, snapshot: Path | None, workers: int, last: date) -> Inputs:
    drive = build_drive_reader()
    cache = InputCache(cache_folder, drive.get)
    sessions = sessions_from_manifests()
    udiff_days, legacy_days = set(cache.days(UDIFF)), set(cache.days(LEGACY))
    names = symbol_names(snapshot_bytes(drive, "names"))
    meeting_files = fetch_meetings(cache_folder, last)
    write_inputs_record(meeting_files)
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
        meetings=[m for _, data in meeting_files for m in read_meetings(data)],
        filing_times=read_filing_times(FILINGS_MANIFEST),
        sectors=read_sectors(snapshot_bytes(drive, "sectors")),
        names=names,
        actions=corporate_actions(snapshot_bytes(drive, "actions"), names),
        charges=load_config()["charges"],
        snapshot=read_snapshot_legs(snapshot) if snapshot else None,
        workers=workers,
    )


def trials_total() -> int:
    with LEDGER.open(newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))
