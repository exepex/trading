"""Downloads NSE daily F&O files (UDiFF format) and keeps only the NIFTY option rows the capacity screen needs.

Run from the repository root:  python research/2026-10-12-capacity-screen/fetch.py
One request at a time, one second apart. Resumable: dates already in the manifest are skipped.
Writes data/nifty_options.csv.gz (NIFTY options, 20-55 calendar days to expiry, strikes within 1,500 points of the
underlying) and data/manifest.csv (every date tried: URL, HTTP status, SHA-256 of the ZIP bytes, rows kept).
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import time as wall_clock
import zipfile
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
URL = "https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{day:%Y%m%d}_F_0000.csv.zip"
FIRST_DAY, LAST_DAY = date(2024, 1, 1), date(2026, 10, 9)
KEEP_DAYS_TO_EXPIRY = (20, 55)
KEEP_STRIKE_DISTANCE = 1500.0
GAP_SECONDS = 1.0
RETRY_WAITS = (5, 15, 45)
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


def fetch(day: date) -> tuple[int | str, bytes]:
    """HTTP status and body. A dropped connection is retried after 5, 15 and 45 seconds, then recorded as an error
    (and retried on the next run, since only completed answers are written to the manifest)."""
    request = Request(URL.format(day=day), headers={"User-Agent": "Mozilla/5.0"})
    for wait in RETRY_WAITS:
        try:
            with urlopen(request, timeout=60) as response:
                return response.status, response.read()
        except HTTPError as exc:
            return exc.code, b""
        except (URLError, OSError):
            wall_clock.sleep(wait)
    return "error", b""


def main() -> None:
    DATA.mkdir(exist_ok=True)
    manifest_path, rows_path = DATA / "manifest.csv", DATA / "nifty_options.csv"
    done = set()
    if manifest_path.exists():
        done = {r["date"] for r in csv.DictReader(manifest_path.open())}
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
                status, body = fetch(day)
                kept = 0
                if status == 200 and body:
                    with zipfile.ZipFile(io.BytesIO(body)) as zf:
                        text = zf.read(zf.namelist()[0]).decode("utf-8")
                    for row in csv.DictReader(io.StringIO(text)):
                        if keep(row, day):
                            rows.writerow(row)
                            kept += 1
                if status == "error":
                    day += timedelta(days=1)
                    continue  # not recorded: the next run asks again
                digest = hashlib.sha256(body).hexdigest() if body else ""
                manifest.writerow({"date": day.isoformat(), "url": URL.format(day=day), "status": status,
                                   "sha256": digest, "rows_kept": kept})  # fmt: skip
                mf.flush()
                rf.flush()
                wall_clock.sleep(GAP_SECONDS)
            day += timedelta(days=1)
    with rows_path.open("rb") as src, gzip.GzipFile(DATA / "nifty_options.csv.gz", "wb", mtime=0) as dst:
        dst.write(src.read())


if __name__ == "__main__":
    main()
