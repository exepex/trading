"""The archived F&O files, read from the stores only (never NSE, never a Drive write; protocol section 3), each day's
file read once for every wanted symbol, in parallel, and cached on local disk outside the repository (derived rows, not
a record; Drive keeps the files). The cache is keyed by the symbols and the day list."""

from __future__ import annotations

import gzip
import hashlib
import pickle
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from edge1study.day_files import DayRows

from fno.fo_bhavcopy import BadFile, read_fo_file
from fno.research_data.nifty_panel import DailyFiles
from fno.storage import wiring
from fno.storage.raw_library import StoredFilesLibrary

from .rows import symbol_rows

CACHE = Path(__file__).resolve().parents[3] / "work" / "edge2"
THREADS = 8


def stored_fo_files() -> list[DailyFiles]:
    """UDiFF first, then legacy, as the NIFTY panel and EDGE1 read them; a reader's library (stores only). The raw
    stores come from the storage wiring's reader list (private there: no public stored F&O reader exists yet)."""
    library = StoredFilesLibrary(wiring._reader_raw_stores())
    return [
        wiring.daily_files(wiring.PANEL_FORMAT_UDIFF, wiring.NseDailyFoSource, library),
        wiring.daily_files(wiring.PANEL_FORMAT_LEGACY, wiring.NseLegacyFoSource, library),
    ]


def rows_on(fo_files: Sequence[DailyFiles], day: date, symbols: Sequence[str]) -> dict[str, DayRows]:
    """Each symbol's rows from the first archived file that has the day; an empty dict when no file has it."""
    for files in fo_files:
        if not files.covers(day):
            continue
        name, data = files.get(day)
        if data is None:
            continue
        try:
            records = read_fo_file(name, data)
        except BadFile:
            continue
        found = {s: symbol_rows(day, records, s, files.label) for s in symbols}
        if any(r.options or r.futures for r in found.values()):
            return found
    return {}


def _key(symbols: Sequence[str], days: Sequence[date]) -> str:
    text = ",".join(symbols) + "|" + ",".join(d.isoformat() for d in days)
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def cached_rows(symbols: Sequence[str], days: Sequence[date], fo_files: Sequence[DailyFiles] | None = None,
                cache: Path = CACHE) -> dict[str, list[DayRows]]:  # fmt: skip
    """Each symbol's rows on every day that has a file, in date order."""
    path = cache / f"{'_'.join(s.lower() for s in symbols)}_{_key(symbols, days)}.pkl.gz"
    if path.is_file():
        return pickle.loads(gzip.decompress(path.read_bytes()))
    files = fo_files if fo_files is not None else stored_fo_files()
    with ThreadPoolExecutor(THREADS) as pool:
        per_day = list(pool.map(lambda d: rows_on(files, d, symbols), days))
    found = {s: [rows[s] for rows in per_day if s in rows] for s in symbols}
    cache.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(pickle.dumps(found)))
    return found
