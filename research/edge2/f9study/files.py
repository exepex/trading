"""F9's day rows for every session, read from the stores only (F1's `stored_fo_files`: never NSE, never a Drive
write), each day's file once for both indices, in parallel, cached outside the repository by symbols and days. F1's
reader is frozen with F1's code hash, so this keeps its own row function (monthly expiries and the futures' open)."""

from __future__ import annotations

import gzip
import hashlib
import pickle
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from f1study.files import stored_fo_files

from fno.fo_bhavcopy import BadFile, read_fo_file

from .rows import MonthlyDay, monthly_rows

CACHE = Path(__file__).resolve().parents[3] / "work" / "edge2"
THREADS = 8


def rows_on(fo_files, day: date, symbols: Sequence[str]) -> dict[str, MonthlyDay]:
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
        found = {s: monthly_rows(day, records, s, files.label) for s in symbols}
        if any(r.options or r.futures for r in found.values()):
            return found
    return {}


def cached_rows(symbols: Sequence[str], days: Sequence[date], cache: Path = CACHE) -> dict[str, dict[date, MonthlyDay]]:
    key = hashlib.sha256((",".join(symbols) + "|" + ",".join(d.isoformat() for d in days)).encode()).hexdigest()[:16]
    path = cache / f"f9_{'_'.join(s.lower() for s in symbols)}_{key}.pkl.gz"
    if path.is_file():
        return pickle.loads(gzip.decompress(path.read_bytes()))
    files = stored_fo_files()
    with ThreadPoolExecutor(THREADS) as pool:
        per_day = list(pool.map(lambda d: rows_on(files, d, symbols), days))
    found = {s: {d: rows[s] for d, rows in zip(days, per_day, strict=True) if s in rows} for s in symbols}
    cache.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(pickle.dumps(found)))
    return found
