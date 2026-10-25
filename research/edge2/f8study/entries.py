"""F8's entry inputs (protocol section 3): each cycle's entry-session NIFTY options of the cycle's expiry with their
opening and closing prices, read from the stores only and cached outside the repository; and the forward at the open
by put-call parity at the strike nearest the previous session's index close."""

from __future__ import annotations

import gzip
import hashlib
import pickle
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from f1study.files import stored_fo_files

from fno.constants import INDEX_OPTION, NIFTY_SYMBOL
from fno.fo_bhavcopy import BadFile, read_fo_file
from fno.research_engine.structures import atm_strike

from .spreads import EntryQuote

CACHE = Path(__file__).resolve().parents[3] / "work" / "edge2"
THREADS = 8


def _number(text: str) -> float:
    try:
        return float(text) if text not in ("", "-") else 0.0
    except ValueError:
        return 0.0


def quotes_of(records: Sequence[dict], expiry: date) -> tuple[EntryQuote, ...]:
    return tuple(EntryQuote(float(r["StrkPric"]), r["OptnTp"], _number(r["OpnPric"]), _number(r["ClsPric"]),
                            int(_number(r["TtlTradgVol"])))
                 for r in records if r["TckrSymb"] == NIFTY_SYMBOL and r["FinInstrmTp"] == INDEX_OPTION
                 and r["XpryDt"][:10] == expiry.isoformat())  # fmt: skip


def entry_quotes(day: date, expiry: date, fo_files) -> tuple[EntryQuote, ...]:
    for files in fo_files:
        if not files.covers(day):
            continue
        name, data = files.get(day)
        if data is None:
            continue
        try:
            found = quotes_of(read_fo_file(name, data), expiry)
        except BadFile:
            continue
        if found:
            return found
    return ()


def cached_entries(pairs: Sequence[tuple[date, date]], cache: Path = CACHE) -> dict[tuple[date, date], tuple]:
    """(entry day, expiry) -> its quotes, each day's file read once."""
    key = hashlib.sha256(",".join(f"{a}/{b}" for a, b in pairs).encode()).hexdigest()[:16]
    path = cache / f"f8_entries_{key}.pkl.gz"
    if path.is_file():
        return pickle.loads(gzip.decompress(path.read_bytes()))
    files = stored_fo_files()
    with ThreadPoolExecutor(THREADS) as pool:
        found = dict(zip(pairs, pool.map(lambda p: entry_quotes(p[0], p[1], files), pairs), strict=True))
    cache.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(pickle.dumps(found)))
    return found


def forward_at_open(quotes: Sequence[EntryQuote], previous_close: float) -> float | None:
    calls = {q.strike: q.open for q in quotes if q.kind == "CE" and q.volume > 0 and q.open > 0}
    puts = {q.strike: q.open for q in quotes if q.kind == "PE" and q.volume > 0 and q.open > 0}
    pairs = calls.keys() & puts.keys()
    if not pairs:
        return None
    k0 = atm_strike(pairs, previous_close)
    return k0 + calls[k0] - puts[k0]
