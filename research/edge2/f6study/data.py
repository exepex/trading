"""F6's inputs (protocol sections 2-4), read from the stores only (never NSE, never a Drive write): each session's
participant OI file, parsed by A8's checked reader, and the NIFTY futures' open, close and lot from the day's F&O file.
Nothing dated after the seal day is read unless the held-out read was opened (`seal.py`). Cached outside the
repository by session list."""

from __future__ import annotations

import gzip
import hashlib
import pickle
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from fno.constants import INDEX_FUTURE, NIFTY_SYMBOL, OI_FUTURE_INDEX, PARTICIPANT_CLIENT, PARTICIPANT_FII
from fno.fo_bhavcopy import BadFile, read_fo_file
from fno.research_data.participant_oi import read_participant_oi
from fno.storage import wiring
from fno.storage.raw_library import StoredFilesLibrary

CACHE = Path(__file__).resolve().parents[3] / "work" / "edge2"
THREADS = 8


@dataclass(frozen=True)
class FutureBar:
    expiry: date
    open: float
    close: float
    lot: int | None  # UDiFF's board lot; None in legacy files (the schedule decides)
    legacy: bool


@dataclass(frozen=True)
class Session:
    day: date
    fii_net: int | None  # FII net index-futures contracts at the day's close; None: no readable file
    client_net: int | None
    futures: tuple[FutureBar, ...]  # NIFTY futures listed that day


def _library():
    return StoredFilesLibrary(wiring._reader_raw_stores())  # the storage wiring's reader stores (see f1study.files)


def oi_nets(day: date, files) -> tuple[int | None, int | None]:
    name, data = files.get(day)
    if data is None:
        return None, None
    try:
        found = read_participant_oi(data, name, day)
    except BadFile:
        return None, None
    return (found.position(PARTICIPANT_FII, OI_FUTURE_INDEX).net,
            found.position(PARTICIPANT_CLIENT, OI_FUTURE_INDEX).net)  # fmt: skip


def _number(text: str) -> float:
    try:
        return float(text) if text not in ("", "-") else 0.0
    except ValueError:
        return 0.0


def nifty_futures(records: Sequence[dict], legacy: bool) -> tuple[FutureBar, ...]:
    bars = []
    for r in records:
        if r["TckrSymb"] != NIFTY_SYMBOL or r["FinInstrmTp"] != INDEX_FUTURE:
            continue
        lot = int(_number(r.get("NewBrdLotQty") or "")) or None
        bars.append(FutureBar(date.fromisoformat(r["XpryDt"][:10]), _number(r["OpnPric"]), _number(r["ClsPric"]), lot,
                              legacy))  # fmt: skip
    return tuple(sorted(bars, key=lambda b: b.expiry))


def futures_on(day: date, fo_files) -> tuple[FutureBar, ...]:
    for files in fo_files:
        if not files.covers(day):
            continue
        name, data = files.get(day)
        if data is None:
            continue
        try:
            bars = nifty_futures(read_fo_file(name, data), files.label == wiring.PANEL_FORMAT_LEGACY)
        except BadFile:
            continue
        if bars:
            return bars
    return ()


def read_session(day: date, oi_files, fo_files) -> Session:
    fii, client = oi_nets(day, oi_files)
    return Session(day, fii, client, futures_on(day, fo_files))


def sessions(days: Sequence[date], cache: Path = CACHE) -> list[Session]:
    key = hashlib.sha256(",".join(d.isoformat() for d in days).encode()).hexdigest()[:16]
    path = cache / f"f6_sessions_{key}.pkl.gz"
    if path.is_file():
        return pickle.loads(gzip.decompress(path.read_bytes()))
    library = _library()
    oi_files = wiring.daily_files("participant-oi", wiring.ParticipantOiSource, library)
    fo_files = [wiring.daily_files(wiring.PANEL_FORMAT_UDIFF, wiring.NseDailyFoSource, library),
                wiring.daily_files(wiring.PANEL_FORMAT_LEGACY, wiring.NseLegacyFoSource, library)]  # fmt: skip
    with ThreadPoolExecutor(THREADS) as pool:
        found = list(pool.map(lambda d: read_session(d, oi_files, fo_files), days))
    cache.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(pickle.dumps(found)))
    return found
