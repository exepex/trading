"""Independent checks of the built NIFTY panel (story A3), written without the panel's own reader.

    python research/2026-10-13-nifty-panel/check_panel.py RAW_FOLDER

RAW_FOLDER is a local copy of the project folder (its `raw/` area, same tree as Drive). For every day the manifest
calls "ok" it re-opens both raw files, checks their SHA-256 against the manifest, counts the NIFTY option and NIFTY
future rows with the plain csv module and compares each count with the manifest and with the panel's rows of that day;
it also checks that every row carries that day's Nifty 50 close (and India VIX close for options) and session kind.
It writes counts.json next to this file (with the size of every panel file per year) and exits 1 on any difference.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import sys
import zipfile
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "research" / "data" / "nifty-panel"
HERE = Path(__file__).resolve().parent
DATASETS = {"udiff": "nse/derivatives/fo-bhavcopy", "legacy": "nse/derivatives/fo-bhavcopy-legacy"}
INDEX_DATASET = "nse/indices/index-close"


def raw_bytes(raw: Path, dataset: str, day: str, name: str) -> bytes:
    return (raw / "raw" / dataset / day[:4] / day[5:7] / name).read_bytes()


RAW_KINDS = {"options": ("OPTIDX", "IDO"), "futures": ("FUTIDX", "IDF")}  # old-format and UDiFF instrument codes


def nifty_counts(data: bytes) -> dict[str, int]:
    """NIFTY option and future rows of a raw F&O file, counted with plain csv."""
    counts = dict.fromkeys(RAW_KINDS, 0)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for r in csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode("utf-8-sig"))):
            for table, (legacy, udiff) in RAW_KINDS.items():
                legacy_row = (r.get("INSTRUMENT", "").strip(), r.get("SYMBOL", "").strip()) == (legacy, "NIFTY")
                if legacy_row or (r.get("FinInstrmTp"), r.get("TckrSymb")) == (udiff, "NIFTY"):
                    counts[table] += 1
    return counts


def closes(data: bytes) -> dict[str, Decimal]:
    rows = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    return {r["Index Name"].strip(): Decimal(r["Closing Index Value"]) for r in rows}


def read_panel(manifest: dict) -> tuple[Counter, dict[tuple[str, str], set]]:
    """Rows per (table, day) and the set of (underlying, vix or None, session) values per (table, day)."""
    rows: Counter = Counter()
    values: dict[tuple[str, str], set] = defaultdict(set)
    for name in sorted(manifest["files"]):
        table = name.split("_")[0]
        with gzip.open(PANEL / name, "rt", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                rows[table, r["date"]] += 1
                vix = Decimal(r["vix"]) if "vix" in r else None
                values[table, r["date"]].add((Decimal(r["underlying"]), vix, r["session"]))
    return rows, values


def check_day(raw: Path, day: str, entry: dict, rows: Counter, values: dict) -> list[str]:
    fo = raw_bytes(raw, DATASETS[entry["source_format"]], day, entry["fo_file"])
    index = raw_bytes(raw, INDEX_DATASET, day, entry["index_file"])
    problems = []
    if (
        hashlib.sha256(fo).hexdigest() != entry["fo_sha256"]
        or hashlib.sha256(index).hexdigest() != entry["index_sha256"]
    ):
        problems.append(f"{day}: SHA-256 differs from the manifest")
    counts, c = nifty_counts(fo), closes(index)
    for table, manifest_key in (("options", "rows"), ("futures", "futures_rows")):
        if not counts[table] == entry[manifest_key] == rows[table, day]:
            problems.append(
                f"{day} {table}: raw {counts[table]}, manifest {entry[manifest_key]}, panel {rows[table, day]}"
            )
    expected = {
        "options": (c["Nifty 50"], c["India VIX"], entry["session"]),
        "futures": (c["Nifty 50"], None, entry["session"]),
    }
    for table, value in expected.items():
        if values[table, day] != {value}:
            problems.append(f"{day} {table}: values {values[table, day]} != {value}")
    return problems


def main(raw: Path) -> int:
    manifest = json.loads((PANEL / "manifest.json").read_text())
    rows, values = read_panel(manifest)
    problems = []
    for day, entry in sorted(manifest["days"].items()):
        if entry["status"] == "ok":
            problems += check_day(raw, day, entry, rows, values)
        elif rows["options", day] or rows["futures", day]:
            problems.append(f"{day}: status {entry['status']} but it has panel rows")
    per_year: dict = defaultdict(dict)
    for (table, day), n in rows.items():
        per_year[day[:4]][f"{table}_rows"] = per_year[day[:4]].get(f"{table}_rows", 0) + n
    for name in manifest["files"]:
        table, year = name.removesuffix(".csv.gz").split("_")
        per_year[year][f"{table}_bytes"] = (PANEL / name).stat().st_size
    for day in manifest["days"]:
        per_year[day[:4]]["sessions_ok"] = per_year[day[:4]].get("sessions_ok", 0) + (
            manifest["days"][day]["status"] == "ok"
        )
    statuses = Counter(e["status"] for e in manifest["days"].values())
    result = {"days_checked": statuses["ok"], "statuses": dict(statuses), "problems": problems, "per_year": per_year}
    (HERE / "counts.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "problems"}, indent=1, sort_keys=True))
    print(f"{len(problems)} problem(s)", *problems[:20], sep="\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
