"""Shared fixtures of the MS-P1d tests: the contracts' builders plus the real charges and a 4-index settlement file.
Fixed values only: no live strike, price or capture."""

import csv
import io
import zipfile
from datetime import date, timedelta
from pathlib import Path

from fno.config import ROOT, load_config
from fno.desk.settlement import NseFinalSettlement
from fno.school.execution.school_fills import SchoolFills
from fno.school.execution.settlement_source import ArchivedOnly, BhavcopySettlement
from fno.storage.raw_library import RawFileLibrary
from fno.storage.raw_source import NseDailyFoSource
from fno.storage.raw_store import LocalFolderStore
from tests.school.contracts import builders as b

CHARGES = load_config(ROOT / "config.yaml")["charges"]
AT = b.SLOT_AT + timedelta(minutes=4)  # after the seal (pushed at +3) and the snapshot's finish (+2)
REAL_DAY = date(2024, 1, 25)  # NSE's 25 Jan 2024 file (NIFTY rows), the template of the settlement fixture
REAL = Path(__file__).parents[2] / "fixtures" / "nse_settlement"
SETTLEMENTS = {"NIFTY": 21352.60, "BANKNIFTY": 45015.25, "FINNIFTY": 20010.50, "MIDCPNIFTY": 10050.75}


def settlement_folder(tmp_path: Path, prices: dict[str, float] = SETTLEMENTS, day: date = REAL_DAY) -> Path:
    """The real file's rows for NIFTY plus one future row per other index, each with its own `SttlmPric`. The same
    arguments always give the same bytes, so a file's SHA-256 can be compared across two builds."""
    path = NseDailyFoSource.path_for(REAL_DAY)
    name = path.rsplit("/", 1)[-1][:-4]
    with zipfile.ZipFile(REAL / path) as original:
        rows = list(csv.DictReader(io.StringIO(original.read(name).decode())))
    template = rows[0]
    out_rows = [r for r in rows if r["XpryDt"] == REAL_DAY.isoformat()] if "NIFTY" in prices else []
    for index, price in prices.items():
        if index != "NIFTY":
            out_rows.append(template | {"TckrSymb": index, "FinInstrmTp": "IDF", "OptnTp": "", "StrkPric": "",
                                        "SttlmPric": f"{price:.2f}", "FinInstrmNm": f"{index}24JANFUT"})  # fmt: skip
    for row in out_rows:
        row |= {"TradDt": day.isoformat(), "BizDt": day.isoformat(), "XpryDt": day.isoformat()}
    text = io.StringIO()
    writer = csv.DictWriter(text, fieldnames=list(template), lineterminator="\n")
    writer.writeheader()
    writer.writerows(out_rows)
    target = tmp_path / NseDailyFoSource.path_for(day)
    target.parent.mkdir(parents=True, exist_ok=True)
    entry = zipfile.ZipInfo(NseDailyFoSource.filename_for(day)[:-4], (day.year, day.month, day.day, 0, 0, 0))
    with zipfile.ZipFile(target, "w") as copy:
        copy.writestr(entry, text.getvalue())  # a fixed stamp: a plain name would take the wall clock into the bytes
    return tmp_path


def settlement_source(folder: Path) -> BhavcopySettlement:
    return BhavcopySettlement(NseFinalSettlement(RawFileLibrary([LocalFolderStore(folder)], ArchivedOnly())))


def fills(folder: Path) -> SchoolFills:
    return SchoolFills(CHARGES, settlement_source(folder))
