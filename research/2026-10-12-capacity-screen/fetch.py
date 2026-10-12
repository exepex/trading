"""Gets NSE daily F&O files and keeps what the capacity screen needs.

Run from the repository root:  python research/2026-10-12-capacity-screen/fetch.py [--rebuild] [--keep-raw FOLDER]
Files come from the raw-file library (fno/storage): a local or Google Drive copy if one exists, otherwise NSE, one
polite request at a time. Every calendar day is asked for (special sessions can fall on a weekend).

Writes three files under data/ that always describe the same set of days:
- manifest.csv: every day asked: URL, status (200 = a file, 404 = no file at that URL), SHA-256, rows kept.
- nifty_expiries.csv.gz: for every day with a file, every NIFTY option expiry listed that day and whether it is the
  monthly one, decided from that day's complete list (expiries.py).
- nifty_options.csv.gz: NIFTY option rows 20-55 calendar days to expiry within 1,500 points of the underlying.

The .gz files are the master copies. A run resumes from them; if the manifest exists without them (or they disagree),
it stops and asks for --rebuild instead of writing anything. Outputs are replaced only when complete.
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
sys.path.insert(0, str(Path(__file__).resolve().parent))

from expiries import monthly_expiries  # noqa: E402

from fno.storage.raw_source import NseDailyFoSource, RawSourceUnavailable  # noqa: E402
from fno.storage.wiring import build_nse_fo_library  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FIRST_DAY, LAST_DAY = date(2024, 1, 1), date(2026, 10, 9)
KEEP_DAYS_TO_EXPIRY = (20, 55)
KEEP_STRIKE_DISTANCE = 1500.0
OPTION_FIELDS = [
    "TradDt", "XpryDt", "StrkPric", "OptnTp", "ClsPric", "PrvsClsgPric", "SttlmPric", "UndrlygPric",
    "TtlTradgVol", "TtlNbOfTxsExctd", "OpnIntrst", "NewBrdLotQty",
]  # fmt: skip
EXPIRY_FIELDS = ["date", "expiry", "days_to_expiry", "monthly"]
MANIFEST_FIELDS = ["date", "url", "status", "sha256", "rows_kept"]
FILES = {"manifest": "manifest.csv", "expiries": "nifty_expiries.csv.gz", "options": "nifty_options.csv.gz"}
SAVE_EVERY_DAYS = 50  # progress is saved this often, so a crash loses little
REBUILD_HINT = "run again with --rebuild to download everything afresh"


class InconsistentData(RuntimeError):
    """The manifest and the extracts do not describe the same days; nothing was written."""


def read_csv(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    """Writes a complete file under a temporary name, then swaps it in."""
    temporary = path.with_name(f".{path.name}.part")
    if path.suffix == ".gz":
        with gzip.GzipFile(temporary, "wb", mtime=0) as raw, io.TextIOWrapper(raw, newline="") as f:
            _write(f, fields, rows)
    else:
        with temporary.open("w", newline="") as f:
            _write(f, fields, rows)
    temporary.replace(path)


def _write(f, fields: list[str], rows: list[dict]) -> None:
    writer = csv.DictWriter(f, fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)


def load_existing(data: Path) -> dict[str, list[dict]]:
    """The three files as they are, checked for consistency; empty lists when nothing exists yet."""
    present = {name: (data / file).exists() for name, file in FILES.items()}
    if not any(present.values()):
        return {name: [] for name in FILES}
    if not all(present.values()):
        missing = [FILES[n] for n, ok in present.items() if not ok]
        raise InconsistentData(f"missing {', '.join(missing)} next to the others; {REBUILD_HINT}")
    existing = {name: read_csv(data / file) for name, file in FILES.items()}
    with_file = {r["date"] for r in existing["manifest"] if r["status"] == "200"}
    if with_file != {r["date"] for r in existing["expiries"]}:
        raise InconsistentData(f"manifest and expiry list cover different days; {REBUILD_HINT}")
    return existing


def extract(zip_bytes: bytes, day: date) -> tuple[list[dict], list[dict]]:
    """From one complete NSE file: that day's NIFTY expiry list (monthly marked) and the option rows kept."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8")
    nifty = [r for r in csv.DictReader(io.StringIO(text)) if r["TckrSymb"] == "NIFTY" and r["FinInstrmTp"] == "IDO"]
    listed = {date.fromisoformat(r["XpryDt"]) for r in nifty}
    monthly = monthly_expiries(listed)
    expiries = [
        {
            "date": day.isoformat(),
            "expiry": e.isoformat(),
            "days_to_expiry": (e - day).days,
            "monthly": int(e in monthly),
        }
        for e in sorted(listed)
    ]
    kept = []
    for row in nifty:
        days = (date.fromisoformat(row["XpryDt"]) - day).days
        near = abs(float(row["StrkPric"]) - float(row["UndrlygPric"])) <= KEEP_STRIKE_DISTANCE
        if KEEP_DAYS_TO_EXPIRY[0] <= days <= KEEP_DAYS_TO_EXPIRY[1] and near:
            kept.append({k: row[k] for k in OPTION_FIELDS})
    return expiries, kept


def save(data: Path, existing: dict[str, list[dict]]) -> None:
    """All three files, each complete; the manifest last because it marks days as done."""
    existing["manifest"].sort(key=lambda r: r["date"])
    write_csv(data / FILES["expiries"], EXPIRY_FIELDS, existing["expiries"])
    write_csv(data / FILES["options"], OPTION_FIELDS, existing["options"])
    write_csv(data / FILES["manifest"], MANIFEST_FIELDS, existing["manifest"])


def update(data: Path, library, first: date, last: date, rebuild: bool = False) -> dict[str, int]:
    """Adds the missing days. --rebuild starts from nothing but replaces the old files only as each save completes."""
    data.mkdir(parents=True, exist_ok=True)
    existing = {name: [] for name in FILES} if rebuild else load_existing(data)
    done = {r["date"] for r in existing["manifest"]}
    added = {"days": 0, "files": 0}
    day = first
    try:
        while day <= last:
            if day.isoformat() not in done:
                path = NseDailyFoSource.path_for(day)
                raw = library.get(path)
                expiries, kept = extract(raw.data, day) if raw.data else ([], [])
                existing["expiries"] += expiries
                existing["options"] += kept
                existing["manifest"].append(
                    {
                        "date": day.isoformat(),
                        "url": NseDailyFoSource.url_for(path),
                        "status": 200 if raw.data else 404,
                        "sha256": hashlib.sha256(raw.data).hexdigest() if raw.data else "",
                        "rows_kept": len(kept),
                    }
                )
                added["days"] += 1
                added["files"] += bool(raw.data)
                if added["days"] % SAVE_EVERY_DAYS == 0:
                    save(data, existing)
            day += timedelta(days=1)
    except (RawSourceUnavailable, KeyboardInterrupt) as exc:
        print(f"stopped early ({type(exc).__name__}); saving the days done so far")
    save(data, existing)
    return added


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="discard the extracts and download every day again")
    parser.add_argument("--keep-raw", type=Path, help="project folder; originals are kept under its raw/ area")
    args = parser.parse_args()
    library = build_nse_fo_library(args.keep_raw)
    try:
        added = update(DATA, library, FIRST_DAY, LAST_DAY, args.rebuild)
    except InconsistentData as exc:
        raise SystemExit(f"nothing written: {exc}") from exc
    print(f"added {added['days']} days ({added['files']} files)")


if __name__ == "__main__":
    main()
