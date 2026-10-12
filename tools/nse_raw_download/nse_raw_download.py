"""Downloads NSE's daily F&O files (2024 onwards) into the fno-research project folder, ready for Google Drive.

Standalone: needs only Python 3.9+ (no packages, no repository). Run on your own computer:

    python nse_raw_download.py --dest "G:/My Drive/fno-research"

Files go to <dest>/raw/nse/derivatives/fo-bhavcopy/<YYYY>/<MM>/<NSE's own file name>, the same layout the research
tool uses (fno/storage). One request per second, so NSE is never flooded. Safe to stop and run again: files already
there are checked and skipped. If manifest.csv (next to this script) lists a file's SHA-256, every download and every
existing file is checked against it. A file that differs is reported and never overwritten.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://nsearchives.nseindia.com/content/fo/"
FILENAME = "BhavCopy_NSE_FO_0_0_0_{day:%Y%m%d}_F_0000.csv.zip"
LAYOUT = "raw/nse/derivatives/fo-bhavcopy/{day:%Y}/{day:%m}/{filename}"  # same as fno/storage (tested in the repo)
FIRST_DAY = date(2024, 1, 2)  # NSE serves this file format from January 2024
GAP_SECONDS = 1.0
RETRY_WAITS = (5, 15, 45)
REFUSED = (403, 429)
USER_AGENT = "Mozilla/5.0 (personal research; one request per second)"


def relative_path(day: date) -> str:
    return LAYOUT.format(day=day, filename=FILENAME.format(day=day))


def load_manifest(path: Path) -> tuple[dict[str, str], set[str]]:
    """date -> expected SHA-256 for days NSE published a file, and the days it published none (holidays)."""
    if not path.is_file():
        return {}, set()
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    expected = {r["date"]: r["sha256"] for r in rows if r.get("status") == "200" and r.get("sha256")}
    return expected, {r["date"] for r in rows if r.get("status") == "404"}


def download(url: str) -> tuple[int, bytes]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    for wait in (*RETRY_WAITS, None):
        try:
            with urlopen(request, timeout=60) as response:
                return response.status, response.read()
        except HTTPError as exc:
            return exc.code, b""
        except (URLError, OSError) as exc:
            if wait is None:
                raise RuntimeError(f"network failure for {url}: {exc}") from exc
            print(f"  connection problem ({exc}); retrying in {wait} s")
            time.sleep(wait)
    raise AssertionError("unreachable")


def save(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.part")
    temporary.write_bytes(data)
    temporary.replace(target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dest", required=True, type=Path, help="the fno-research project folder")
    parser.add_argument("--start", type=date.fromisoformat, default=FIRST_DAY, help="first date, YYYY-MM-DD")
    parser.add_argument("--end", type=date.fromisoformat, default=date.today(), help="last date, YYYY-MM-DD")
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("manifest.csv"))
    args = parser.parse_args()
    expected, holidays = load_manifest(args.manifest)
    counts = {"saved": 0, "already there": 0, "no file (holiday)": 0, "mismatch": 0}
    day = args.start
    while day <= args.end:
        if day.weekday() >= 5 or day.isoformat() in holidays:
            day += timedelta(days=1)
            continue
        target = args.dest / relative_path(day)
        want = expected.get(day.isoformat())
        if target.is_file():
            have = hashlib.sha256(target.read_bytes()).hexdigest()
            if want and have != want:
                print(f"MISMATCH {day}: existing file differs from the recorded fingerprint; left untouched")
                counts["mismatch"] += 1
            else:
                counts["already there"] += 1
            day += timedelta(days=1)
            continue
        status, data = download(BASE_URL + FILENAME.format(day=day))
        if status in REFUSED:
            print(f"NSE refused the request (HTTP {status}). Stopping to avoid a block; run again later.")
            break
        if status == 404:
            counts["no file (holiday)"] += 1
        elif status == 200:
            got = hashlib.sha256(data).hexdigest()
            if want and got != want:
                print(f"MISMATCH {day}: NSE's file differs from the recorded fingerprint; not saved")
                counts["mismatch"] += 1
            else:
                save(target, data)
                counts["saved"] += 1
                print(f"saved {target.relative_to(args.dest)} ({len(data) / 1e6:.1f} MB)")
        else:
            print(f"{day}: unexpected HTTP {status}; skipped (run again later)")
        time.sleep(GAP_SECONDS)
        day += timedelta(days=1)
    print("; ".join(f"{k}: {v}" for k, v in counts.items()))
    return 1 if counts["mismatch"] else 0


if __name__ == "__main__":
    sys.exit(main())
