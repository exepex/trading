"""Composition root of the filings archive (story A12): the only place that picks the concrete exchange lists, sources
and stores for filings. Swapping NSE for BSE, or Drive for another store, changes this file only.
"""

from __future__ import annotations

import hashlib
from datetime import date

from ..market_read_models.nse_files import read_nifty500_list
from ..models import now_ist
from ..providers.public import PublicData
from ..storage import wiring as storage
from ..storage.coverage import CoverageDataset
from ..storage.librarian import RawDataLibrarian
from ..storage.manifest_folder import FingerprintingStore
from ..storage.raw_store import AreaStore, RawFileStore, StoredCopyDamaged
from ..storage.snapshot_source import Nifty500ListSource
from .archive import FilingArchive
from .coverage import FilingsCoverage
from .day_lists import EveryDayCalendar, check_day_list
from .gaps import GapLog
from .index import NseIntegratedResultsIndex, NseLegacyResultsIndex, NseShareholdingIndex
from .librarian import FilingsLibrarian
from .manifest import FilingManifest
from .results_table import ResultsTable
from .runs import RunLog
from .sources import NseAnnouncementsSource, NseBoardMeetingsSource, NseFilingFileSource

FILINGS_MANIFEST_FOLDER = storage.MANIFEST_FOLDER / "filings"
GAPS_FILE = FILINGS_MANIFEST_FOLDER / "gaps.csv"
RUNS_FILE = FILINGS_MANIFEST_FOLDER / "runs.csv"
BACKFILL_SINCE = date(2023, 10, 1)  # three years, from the first results of the September 2023 half-year on
NIFTY500_SNAPSHOT_DAY = date(2026, 10, 13)  # the archived Nifty 500 list the company list comes from (P6)
DAY_LIST_SOURCES = (NseAnnouncementsSource, NseBoardMeetingsSource)
DAY_LISTS = {s.dataset.rsplit("/", 1)[-1]: s for s in DAY_LIST_SOURCES}
UPLOAD_SETTINGS_MISSING = f"set {', '.join(storage.OWNER_UPLOAD_SETTINGS)} to upload to Drive"


def build_filings_manifest() -> FilingManifest:
    return FilingManifest(FILINGS_MANIFEST_FOLDER)


def _owner_raw_area() -> RawFileStore:
    drive = storage.build_owner_drive()
    if drive is None:
        raise RuntimeError(UPLOAD_SETTINGS_MISSING)
    return AreaStore(drive, storage.RAW_AREA)


def build_filings_librarian(log=print) -> FilingsLibrarian:
    """NSE's filing lists and XBRL files into the owner's Drive, each file with its manifest row."""
    get_json = PublicData().nse_json
    indexes = (NseLegacyResultsIndex(get_json), NseIntegratedResultsIndex(get_json), NseShareholdingIndex(get_json))
    archive = FilingArchive(_owner_raw_area(), build_filings_manifest(), now_ist)
    return FilingsLibrarian(indexes, storage.build_nse_source(NseFilingFileSource), archive, now_ist, log)


def build_day_list_librarian(name: str, log=print) -> RawDataLibrarian:
    """One all-company day list (a key of DAY_LISTS) into the owner's Drive, with its manifest row per day."""
    source_type = DAY_LISTS[name]
    manifests = storage.build_manifest_folder()
    store = FingerprintingStore(_owner_raw_area(), manifests, DAY_LIST_SOURCES)
    dataset = CoverageDataset(source_type, check_day_list, manifests.fingerprints(source_type))
    source = storage.build_nse_source(source_type)
    return RawDataLibrarian(store, source, dataset, EveryDayCalendar(), {}, log)


def build_companies() -> list[str]:
    """The Nifty 500's symbols from the archived list in Drive, checked against its manifest's SHA-256."""
    path = Nifty500ListSource.path_for(NIFTY500_SNAPSHOT_DAY)
    data = storage.build_drive_reader().get(path)
    want = storage.build_manifest_folder().fingerprints(Nifty500ListSource).get(Nifty500ListSource.FILENAME)
    if data is None or hashlib.sha256(data).hexdigest() != want:
        raise StoredCopyDamaged(f"{path}: missing in Drive or not the manifest's SHA-256")
    return sorted(read_nifty500_list(data, Nifty500ListSource.FILENAME))


def build_filings_coverage() -> FilingsCoverage:
    return FilingsCoverage(storage.build_drive_reader(), build_filings_manifest(), GapLog(GAPS_FILE).read())


def build_results_table() -> ResultsTable:
    """Reported results as known at a moment, read only from Drive (service account)."""
    return ResultsTable(build_filings_manifest(), storage.build_drive_reader())


def build_gap_log() -> GapLog:
    return GapLog(GAPS_FILE)


def build_run_log() -> RunLog:
    return RunLog(RUNS_FILE)
