"""Story C4 fixtures for the sources judge 83 added: NSE's daily F&O file of the previous session (lot sizes and
listed expiries), a book's account as C4 reads it, A14's three-part margin rows and the owner's limits with a
stressed-margin factor set."""

from __future__ import annotations

import copy
import csv
import io
import zipfile
from dataclasses import replace
from datetime import date

from fno.checks.validity_account import AccountFacts, Position
from fno.checks.validity_settings import limits_from_config
from fno.config import ROOT, load_config
from fno.fo_bhavcopy import COLUMNS
from fno.storage.raw_library import RawFile
from fno.storage.raw_source import NseDailyFoSource

FILE_DAY = date(2026, 10, 13)  # the session before the decision day, 14 Oct 2026
EXPIRIES = ("2026-10-20", "2026-10-27", "2026-11-03", "2026-11-24")  # two weeklies; October's and November's monthly
START = 500_000.0


def nse_file(lot: int = 65, expiries=EXPIRIES, strikes=range(24_400, 25_650, 50)) -> bytes:
    """A UDiFF F&O file: NIFTY index options on each expiry with NSE's lot size, plus a stock option and a BANKNIFTY
    option (a later October expiry, another lot) that must be ignored."""
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    base = dict.fromkeys(COLUMNS, "") | {"TradDt": FILE_DAY.isoformat(), "Sgmt": "FO", "Src": "NSE"}
    for expiry in expiries:
        for strike in strikes:
            for kind in ("CE", "PE"):
                writer.writerow(base | {"FinInstrmTp": "IDO", "TckrSymb": "NIFTY", "XpryDt": expiry,
                                        "StrkPric": f"{strike}", "OptnTp": kind, "NewBrdLotQty": f"{lot}"})  # fmt: skip
    stock = {"FinInstrmTp": "STO", "TckrSymb": "RELIANCE", "XpryDt": "2026-10-29", "NewBrdLotQty": "500"}
    bank = {"FinInstrmTp": "IDO", "TckrSymb": "BANKNIFTY", "XpryDt": "2026-10-28", "NewBrdLotQty": "30"}
    writer.writerows([base | stock, base | bank])  # other contracts: never NIFTY's lot or expiries
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr(NseDailyFoSource.filename_for(FILE_DAY).removesuffix(".zip"), out.getvalue())
    return data.getvalue()


class NseFiles:
    """A raw-file library holding NSE's F&O file of these days."""

    def __init__(self, files: dict[date, bytes] | None = None):
        self.files = {
            NseDailyFoSource.path_for(d): data
            for d, data in ({FILE_DAY: nse_file()} if files is None else files).items()
        }

    def get(self, path: str) -> RawFile:
        return RawFile(self.files.get(path), "test")


def fresh_account(**changes) -> AccountFacts:
    """Rs 5 lakh, no trades yet."""
    return replace(AccountFacts(START, ((date(2026, 10, 1), START),), ()), **changes)


class Accounts:
    def __init__(self, facts: AccountFacts | None = None):
        self.given = facts or fresh_account()

    def facts(self, book, cutoff) -> AccountFacts:
        return self.given


MARGIN_ROWS = [
    {"structure": s, "width": f"{w}", "scan_per_lot_rs": f"{scan}", "nov_per_lot_rs": f"{nov}",
     "exposure_per_lot_rs": f"{exposure}", "source": "test fixture", "as_of": FILE_DAY.isoformat()}
    for s, w, scan, nov, exposure in (
        ("SF", 200, 9_000.0, -10_270.0, 65_000.0), ("SC", 100, 7_500.0, -1_650.0, 65_000.0),
        ("BF", 100, 1_500.0, 5_750.0, 65_000.0), ("BF", 200, 3_000.0, 10_270.0, 65_000.0),
    )
]  # fmt: skip


class Margins:
    def __init__(self, rows=None):
        self.given = MARGIN_ROWS if rows is None else rows

    def rows(self):
        return self.given


def limits(**risk_changes):
    """config.yaml's limits with a stressed-margin factor of 1.45 set (dated, sourced) and these `risk` changes."""
    cfg = copy.deepcopy(load_config(ROOT / "config.yaml"))
    cfg["risk"]["stressed_margin"] |= {"multiplier": 1.45, "source": "test fixture", "as_of": FILE_DAY.isoformat()}
    cfg["risk"] |= risk_changes
    return limits_from_config(cfg, ROOT)


def held(trade_id: str, units: dict[str, int], cash_flow: float = 0.0) -> Position:
    return Position(trade_id, units, cash_flow)
