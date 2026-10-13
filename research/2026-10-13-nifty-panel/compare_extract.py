"""Story A3 criterion 10: the panel's 2024-2026 rows reproduce the capacity screen's extract.

    python research/2026-10-13-nifty-panel/compare_extract.py

For every contract in research/2026-10-12-capacity-screen/data/nifty_options.csv.gz (NIFTY options 20-55 days to
expiry within 1,500 points, read from the UDiFF files) the panel must hold the same (date, expiry, strike, type) with
the same close, settlement price, volume and open interest, and an underlying equal to the extract's UDiFF
underlying (the panel takes it from NSE's index-close file). Also compares the days. Writes compare_extract.json.
"""

from __future__ import annotations

import csv
import gzip
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "research" / "data" / "nifty-panel"
EXTRACT = ROOT / "research" / "2026-10-12-capacity-screen" / "data" / "nifty_options.csv.gz"
EXTRACT_MANIFEST = ROOT / "research" / "2026-10-12-capacity-screen" / "data" / "manifest.csv"
HERE = Path(__file__).resolve().parent
FIELDS = {"close": "ClsPric", "settle": "SttlmPric", "volume": "TtlTradgVol", "open_interest": "OpnIntrst",
          "underlying": "UndrlygPric"}  # fmt: skip


def read(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    extract = {(r["TradDt"], r["XpryDt"], Decimal(r["StrkPric"]), r["OptnTp"]): r for r in read(EXTRACT)}
    first, last = min(k[0] for k in extract), max(k[0] for k in extract)
    panel = {}
    for year in range(int(first[:4]), int(last[:4]) + 1):
        for r in read(PANEL / f"options_{year}.csv.gz"):
            if first <= r["date"] <= last:
                panel[(r["date"], r["expiry"], Decimal(r["strike"]), r["type"])] = r
    with EXTRACT_MANIFEST.open(newline="") as f:
        extract_days = {r["date"] for r in csv.DictReader(f) if r["status"] == "200" and first <= r["date"] <= last}
    panel_days = {k[0] for k in panel}
    missing = sorted(map(str, set(extract) - set(panel)))
    differences = []
    for key, row in extract.items():
        if key in panel:
            for ours, theirs in FIELDS.items():
                if Decimal(panel[key][ours]) != Decimal(row[theirs]):
                    differences.append(
                        f"{key[0]} {key[1]} {key[2]} {key[3]} {ours}: {panel[key][ours]} vs {row[theirs]}"
                    )
    result = {
        "range": [first, last],
        "extract_contracts": len(extract),
        "found_in_panel": len(extract) - len(missing),
        "missing_from_panel": missing[:50],
        "value_differences": len(differences),
        "first_differences": differences[:50],
        "days_with_a_file_in_extract_manifest": len(extract_days),
        "days_in_panel": len(panel_days),
        "days_only_in_extract": sorted(extract_days - panel_days),
        "days_only_in_panel": sorted(panel_days - extract_days),
        "panel_contracts_in_range": len(panel),
    }
    (HERE / "compare_extract.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))
    same_days = extract_days == panel_days
    return 0 if not missing and not differences and same_days else 1


if __name__ == "__main__":
    sys.exit(main())
