"""Composition root of study FT1: the panel, NSE's session calendar, India VIX, the A16b index candles in Drive, the
contracts' archive in the owner's Drive, A4's quotes and Groww's contract candles through A16's read-only client. No
order code: the only Groww object is `ReadOnlyGroww`."""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fno.composition import build_tradable_structures
from fno.config import load_app_config
from fno.constants import NIFTY_SYMBOL
from fno.intraday.candle_archive import CandleArchive
from fno.intraday.read_only import ReadOnlyGroww
from fno.providers.groww import GrowwProvider
from fno.quotes.report import canonical_snapshots
from fno.storage.raw_store import AreaStore
from fno.storage.wiring import (
    MANIFEST_FOLDER,
    QUOTES_FOLDER,
    RAW_AREA,
    build_drive_reader,
    build_owner_drive,
    build_quote_store,
    build_session_calendar,
)

from .archive import MANIFEST_NAME, ContractArchive
from .bars import ArchivedPrices, BarBook
from .candles import GrowwContractCandles
from .contracts import REPOSITORY, read_panel
from .entries import IndexLevels
from .fetch import Fetcher, MarketHours
from .observe import Market, Observer, Terms

IST = timezone(timedelta(hours=5, minutes=30))
PANEL_YEARS = (2024, 2025, 2026)
WINDOW_FIRST, WINDOW_LAST = date(2024, 1, 2), date(2026, 9, 30)
CANDLE_MANIFESTS = MANIFEST_FOLDER / "groww-candles"
VIX_FILE = REPOSITORY / "research" / "data" / "vix" / "india_vix_daily.csv"
CACHE = Path.home() / ".cache" / "ft1-study"
INDEX_KIND = "15m"


def now_ist() -> datetime:
    return datetime.now(IST)


def build_contract_candles() -> GrowwContractCandles:
    provider = GrowwProvider(load_app_config(None))
    return GrowwContractCandles(ReadOnlyGroww(lambda: provider.api), now_ist)  # the only Groww object it holds


def build_contracts():
    return read_panel(PANEL_YEARS)


def build_calendar():
    return build_session_calendar()


def build_structures():
    return build_tradable_structures()


def build_archive() -> ContractArchive:
    drive = build_owner_drive()
    if drive is None:
        raise RuntimeError("set the four FNO_GDRIVE_* settings to keep and read the candles in Drive")
    return ContractArchive(AreaStore(drive, RAW_AREA), CANDLE_MANIFESTS / MANIFEST_NAME, CACHE)


def build_fetcher(archive: ContractArchive) -> Fetcher:
    return Fetcher(build_contract_candles(), archive, MarketHours(build_calendar(), now_ist))


def build_index_levels() -> IndexLevels:
    copies = CandleArchive(build_drive_reader(), CANDLE_MANIFESTS).copies(INDEX_KIND, WINDOW_FIRST, date.today())
    return IndexLevels(BarBook(copy.rows for copy in copies))


def read_vix_open(path: Path = VIX_FILE) -> dict[date, float]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {date.fromisoformat(r["date"]): float(r["open"]) for r in csv.DictReader(handle)}


def build_terms() -> Terms:
    cfg = load_app_config(None)
    return Terms(lot=cfg["lot_sizes"][NIFTY_SYMBOL], charges=cfg["charges"], rate=cfg["risk_free_rate"])


def build_observer(archive: ContractArchive, contracts, index: IndexLevels, terms: Terms) -> Observer:
    calendar = build_calendar()
    market = Market(ArchivedPrices(archive.copies).bar, index, read_vix_open(), contracts.settlement,
                    calendar.next_session)  # fmt: skip
    return Observer(market, terms)


def read_a4_snapshots() -> list[str]:
    return canonical_snapshots(QUOTES_FOLDER, build_quote_store(QUOTES_FOLDER))  # Groww's, as `fno quotes report`


def sessions_before(calendar):
    def back(day: date, n: int) -> date:
        for _ in range(n):
            day = calendar.previous_session(day)
        return day

    return back


def window_expiries(contracts) -> list[date]:
    """Monthly expiries any decision day of the window can use (the last one lies after the window's end)."""
    later = [e for e in contracts.expiries if e > WINDOW_LAST]
    return [e for e in contracts.expiries if WINDOW_FIRST <= e <= WINDOW_LAST] + later[:1]
