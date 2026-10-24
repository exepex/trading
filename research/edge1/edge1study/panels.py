"""The two indices' daily option panels in the engine's `NiftyPanel` shape (protocol section 3), and each expiry's lot.

- NIFTY: the committed end-of-day panel (`read_nifty_panel`), unchanged. Its lots come from the same F&O files as
  BANKNIFTY's (`lots.py`).
- BANKNIFTY: every session's rows from the archived F&O files (`day_files.py`), with the index close from G13b's close
  table. The first build reads every file once (slow, through Drive), and is cached in `work/edge1/` (git-ignored);
  the cache is keyed by the day list, so a different period rebuilds."""

from __future__ import annotations

import gzip
import hashlib
import pickle
from collections.abc import Callable, Iterable, Sequence
from datetime import date
from pathlib import Path

from fno.research_data.nifty_panel import DailyFiles
from fno.research_data.panel_reader import NiftyPanel, SessionClose

from .day_files import DayRows, day_rows

CACHE = Path(__file__).resolve().parents[3] / "work" / "edge1"


def panel_from_rows(rows: Iterable[DayRows], closes: Callable[[date], float | None],
                    kinds: dict[date, str]) -> NiftyPanel:  # fmt: skip
    """A `NiftyPanel` from day rows: sessions in date order with the index close, options and futures by day."""
    ordered = sorted(rows, key=lambda r: r.day)
    sessions = tuple(SessionClose(r.day, kinds.get(r.day, "regular"), closes(r.day), None) for r in ordered)
    return NiftyPanel(sessions, {r.day: r.options for r in ordered}, {r.day: r.futures for r in ordered})


def _key(days: Sequence[date]) -> str:
    return hashlib.sha256(",".join(d.isoformat() for d in days).encode()).hexdigest()[:16]


def cached_rows(symbols: Sequence[str], days: Sequence[date], fo_files: Sequence[DailyFiles],
                options_for: Sequence[str] = (), cache: Path = CACHE) -> dict[str, list[DayRows]]:  # fmt: skip
    """Each symbol's rows on every day (days with no file are left out), each file read once, the result cached;
    monthly options only for the symbols in `options_for`."""
    name = "_".join(s.lower() + ("+o" if s in options_for else "") for s in symbols)
    path = cache / f"{name}_{_key(days)}.pkl.gz"
    if path.is_file():
        return pickle.loads(gzip.decompress(path.read_bytes()))
    found = {s: [] for s in symbols}
    for day in days:
        for symbol, rows in day_rows(fo_files, day, symbols, options_for).items():
            found[symbol].append(rows)
    cache.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(pickle.dumps(found)))
    return found
