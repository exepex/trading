"""Independent checks of the built NIFTY panel (story A3), written without the panel's own reader.

    python research/2026-10-13-nifty-panel/check_panel.py RAW_FOLDER

RAW_FOLDER is a local copy of the project folder (its `raw/` area, same tree as Drive). For every day the manifest
calls "ok" it re-opens both raw files, checks their SHA-256 against the manifest, counts the NIFTY option rows with
the plain csv module and compares that count with the manifest and with the panel's rows of that day; it also checks
that every panel row carries that day's Nifty 50 and India VIX closes. It writes counts.json next to this file (and
the size of every panel file per year) and exits 1 on any difference.
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


def nifty_option_count(data: bytes) -> int:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        rows = csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode("utf-8-sig")))
        return sum(
            1
            for r in rows
            if (r.get("INSTRUMENT", "").strip(), r.get("SYMBOL", "").strip()) == ("OPTIDX", "NIFTY")
            or (r.get("FinInstrmTp"), r.get("TckrSymb")) == ("IDO", "NIFTY")
        )


def closes(data: bytes) -> dict[str, Decimal]:
    rows = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    return {r["Index Name"].strip(): Decimal(r["Closing Index Value"]) for r in rows}


def main(raw: Path) -> int:
    manifest = json.loads((PANEL / "manifest.json").read_text())
    panel_rows: Counter = Counter()
    panel_values: dict[str, set] = defaultdict(set)
    for name in sorted(manifest["files"]):
        with gzip.open(PANEL / name, "rt", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                panel_rows[r["date"]] += 1
                panel_values[r["date"]].add((Decimal(r["underlying"]), Decimal(r["vix"])))
    problems = []
    for day, entry in sorted(manifest["days"].items()):
        if entry["status"] != "ok":
            if panel_rows[day]:
                problems.append(f"{day}: status {entry['status']} but {panel_rows[day]} panel rows")
            continue
        fo = raw_bytes(raw, DATASETS[entry["source_format"]], day, entry["fo_file"])
        index = raw_bytes(raw, INDEX_DATASET, day, entry["index_file"])
        if (
            hashlib.sha256(fo).hexdigest() != entry["fo_sha256"]
            or hashlib.sha256(index).hexdigest() != entry["index_sha256"]
        ):
            problems.append(f"{day}: SHA-256 differs from the manifest")
        count = nifty_option_count(fo)
        if not count == entry["rows"] == panel_rows[day]:
            problems.append(f"{day}: raw {count}, manifest {entry['rows']}, panel {panel_rows[day]}")
        c = closes(index)
        if panel_values[day] != {(c["Nifty 50"], c["India VIX"])}:
            problems.append(f"{day}: underlying/vix {panel_values[day]} != closes {c['Nifty 50']}, {c['India VIX']}")
    per_year = defaultdict(lambda: {"sessions": 0, "rows": 0})
    for day, n in panel_rows.items():
        per_year[day[:4]]["sessions"] += 1
        per_year[day[:4]]["rows"] += n
    for name in manifest["files"]:
        per_year[name[8:12]]["bytes"] = (PANEL / name).stat().st_size
    statuses = Counter(e["status"] for e in manifest["days"].values())
    result = {"days_checked": statuses["ok"], "statuses": dict(statuses), "problems": problems, "per_year": per_year}
    (HERE / "counts.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "problems"}, indent=1, sort_keys=True))
    print(f"{len(problems)} problem(s)", *problems[:20], sep="\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
