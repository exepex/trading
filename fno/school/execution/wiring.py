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


def build_settlement_source(project_folder: Path | None = None) -> BhavcopySettlement:
    return BhavcopySettlement(NseFinalSettlement(RawFileLibrary(build_raw_stores(project_folder), ArchivedOnly())))


def build_fill_port(cfg: dict, project_folder: Path | None = None) -> SchoolFills:
    return SchoolFills(cfg["charges"], build_settlement_source(project_folder))


def build_capture_1515(root: Path = ROOT) -> RecordedCapture1515:
    return RecordedCapture1515(root, RecordedExecutionSnapshots(build_quote_store()))
