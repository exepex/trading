"""Gets NSE daily F&O files and keeps only the NIFTY option rows the capacity screen needs.

Run from the repository root:  python research/2026-10-12-capacity-screen/fetch.py [--keep-raw FOLDER]
Files come from the raw-file library (fno/storage): a local or Google Drive copy if one exists, otherwise NSE, one
polite request at a time. --keep-raw saves every original ZIP into FOLDER (for example a Google Drive for desktop
folder). Resumable: dates already in the manifest are skipped.
Writes data/nifty_options.csv.gz (NIFTY options, 20-55 calendar days to expiry, strikes within 1,500 points of the
underlying) and data/manifest.csv (every date tried: URL, status 200 = file / 404 = none, SHA-256 of the ZIP bytes,
rows kept).
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fno.storage.raw_source import NseDailyFoSource, RawSourceUnavailable  # noqa: E402
from fno.storage.wiring import build_nse_fo_library  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FIRST_DAY, LAST_DAY = date(2024, 1, 1), date(2026, 10, 9)
KEEP_DAYS_TO_EXPIRY = (20, 55)
KEEP_STRIKE_DISTANCE = 1500.0
FIELDS = [
    "TradDt", "XpryDt", "StrkPric", "OptnTp", "ClsPric", "PrvsClsgPric", "SttlmPric", "UndrlygPric",
    "TtlTradgVol", "TtlNbOfTxsExctd", "OpnIntrst", "NewBrdLotQty",
]  # fmt: skip
MANIFEST_FIELDS = ["date", "url", "status", "sha256", "rows_kept"]


def keep(row: dict, day: date) -> bool:
    if row["TckrSymb"] != "NIFTY" or row["FinInstrmTp"] != "IDO":
        return False
    days = (date.fromisoformat(row["XpryDt"]) - day).days
    if not KEEP_DAYS_TO_EXPIRY[0] <= days <= KEEP_DAYS_TO_EXPIRY[1]:
        return False
    return abs(float(row["StrkPric"]) - float(row["UndrlygPric"])) <= KEEP_STRIKE_DISTANCE


def kept_rows(zip_bytes: bytes, day: date) -> list[dict]:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8")
    return [row for row in csv.DictReader(io.StringIO(text)) if keep(row, day)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep-raw", type=Path, help="folder to keep every original ZIP in")
    library = build_nse_fo_library(parser.parse_args().keep_raw)
    DATA.mkdir(exist_ok=True)
    manifest_path, rows_path = DATA / "manifest.csv", DATA / "nifty_options.csv"
    done = {r["date"] for r in csv.DictReader(manifest_path.open())} if manifest_path.exists() else set()
    new_manifest = not manifest_path.exists()
    with manifest_path.open("a", newline="") as mf, rows_path.open("a", newline="") as rf:
        manifest = csv.DictWriter(mf, MANIFEST_FIELDS)
        rows = csv.DictWriter(rf, FIELDS, extrasaction="ignore")
        if new_manifest:
            manifest.writeheader()
            rows.writeheader()
        day = FIRST_DAY
        while day <= LAST_DAY:
            if day.weekday() < 5 and day.isoformat() not in done:
                filename = NseDailyFoSource.filename_for(day)
                try:
                    raw = library.get(filename)
                except RawSourceUnavailable as exc:
                    print(f"skipped for now: {exc}")  # not recorded, so the next run asks again
                    day += timedelta(days=1)
                    continue
                found = kept_rows(raw.data, day) if raw.data else []
                rows.writerows(found)
                manifest.writerow(
                    {
                        "date": day.isoformat(),
                        "url": NseDailyFoSource.BASE_URL + filename,
                        "status": 200 if raw.data else 404,
                        "sha256": hashlib.sha256(raw.data).hexdigest() if raw.data else "",
                        "rows_kept": len(found),
                    }
                )
                mf.flush()
                rf.flush()
            day += timedelta(days=1)
    with rows_path.open("rb") as src, gzip.GzipFile(DATA / "nifty_options.csv.gz", "wb", mtime=0) as dst:
        dst.write(src.read())


if __name__ == "__main__":
    main()
