"""Composition root of `fno/school/execution/` (story MS-P1d): the fill port (E4's pricing, C1's charges), expiry
settlement over the already-archived F&O bhavcopy (stores only, never NSE), and E3's 15:15 capture for the NIFTY
drift diagnostic."""

from pathlib import Path

from ...config import ROOT
from ...desk.settlement import NseFinalSettlement
from ...desk.snapshot import RecordedExecutionSnapshots
from ...storage.raw_library import RawFileLibrary
from ...storage.wiring import build_quote_store, build_raw_stores
from .capture_1515 import RecordedCapture1515
from .school_fills import SchoolFills
from .settlement_source import ArchivedOnly, BhavcopySettlement


class SettlementStoresNotConfigured(RuntimeError):
    """No store can be read for NSE's archived F&O files: settlement would wait forever while expired positions count
    at their worst case, so the run stops here, by name (judge 486 finding 2). b's `build_archive_stores` (the owner's
    Drive as a fallback) replaces this check once MS-P1b is merged."""


def build_settlement_source(project_folder: Path | None = None) -> BhavcopySettlement:
    stores = build_raw_stores(project_folder)
    if not stores:
        raise SettlementStoresNotConfigured("no store holds NSE's archived F&O files: set the Drive settings")
    return BhavcopySettlement(NseFinalSettlement(RawFileLibrary(stores, ArchivedOnly())))


def build_fill_port(cfg: dict, project_folder: Path | None = None) -> SchoolFills:
    return SchoolFills(cfg["charges"], build_settlement_source(project_folder))


def build_capture_1515(root: Path = ROOT) -> RecordedCapture1515:
    return RecordedCapture1515(root, RecordedExecutionSnapshots(build_quote_store()))
