"""Proves the old-format reader against the current format on every day NSE published both (1 Jan - 5 Jul 2024).

Run from the repository root:  python research/2026-10-12-legacy-format/validate_overlap.py   (writes overlap.json)
Current-format files come from the stores (Google Drive) or NSE; old-format and index-close files from NSE.
For each day: the same contracts in both, every shared field equal as a number, and the underlying price of each
index option (taken from NSE's index close for old files) equal to the one UDiFF reports.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fno.fo_bhavcopy import COLUMNS, LEGACY_FIELDS, read_fo_file, read_index_closes  # noqa: E402
from fno.storage.raw_source import NseDailyFoSource, NseIndexCloseSource, NseLegacyFoSource  # noqa: E402
from fno.storage.wiring import (  # noqa: E402
    build_nse_fo_library,
    build_nse_index_close_library,
    build_nse_legacy_fo_library,
)

FIRST, LAST = date(2024, 1, 1), date(2024, 7, 5)  # the days both formats exist
KEY = ("FinInstrmTp", "TckrSymb", "XpryDt", "StrkPric", "OptnTp")
NUMERIC = (*LEGACY_FIELDS, "TtlTrfVal")
TRADE_VALUE_TOLERANCE = 1000.0  # rupees: the old file rounds traded value to 0.01 lakh


def key(record: dict) -> tuple:
    return tuple(float(record[k]) if k == "StrkPric" and record[k] else record[k] for k in KEY)


def compare(day: date, current: list[dict], legacy: list[dict]) -> dict:
    new, old = {key(r): r for r in current}, {key(r): r for r in legacy}
    result = {"rows": len(new), "only_current": len(set(new) - set(old)), "only_legacy": len(set(old) - set(new))}
    mismatches = {}
    for field in (*NUMERIC, "UndrlygPric", "TradDt"):
        bad = 0
        for k in set(new) & set(old):
            a, b = new[k][field], old[k][field]
            if field == "UndrlygPric" and (k[0] not in ("IDO", "IDF") or not b):
                continue  # stock underlyings are not filled from old files
            if field == "TradDt":
                bad += a != b
            elif field == "TtlTrfVal":
                bad += abs(float(a or 0) - float(b or 0)) > TRADE_VALUE_TOLERANCE
            else:
                bad += abs(float(a or 0) - float(b or 0)) > 1e-6
        mismatches[field] = bad
    result["mismatches"] = mismatches
    result["index_underlyings_checked"] = sum(
        1 for k in set(new) & set(old) if k[0] in ("IDO", "IDF") and old[k]["UndrlygPric"]
    )
    result["index_rows"] = sum(1 for k in new if k[0] in ("IDO", "IDF"))
    return result


def main():
    current_lib, legacy_lib, index_lib = (
        build_nse_fo_library(),
        build_nse_legacy_fo_library(),
        build_nse_index_close_library(),
    )
    days, day = {}, FIRST
    while day <= LAST:
        legacy_file = legacy_lib.get(NseLegacyFoSource.path_for(day))
        current_file = current_lib.get(NseDailyFoSource.path_for(day))
        if legacy_file.data is None or current_file.data is None:
            if (legacy_file.data is None) != (current_file.data is None):
                days[day.isoformat()] = {"error": "published in one format only"}
            day += timedelta(days=1)
            continue
        closes = read_index_closes(index_lib.get(NseIndexCloseSource.path_for(day)).data)
        legacy = read_fo_file(NseLegacyFoSource.filename_for(day), legacy_file.data, closes)
        current = read_fo_file(NseDailyFoSource.filename_for(day), current_file.data)
        days[day.isoformat()] = compare(day, current, legacy)
        print(day, days[day.isoformat()], flush=True)
        day += timedelta(days=1)
    clean = [d for d, r in days.items() if "error" not in r and not r["only_current"] and not r["only_legacy"]
             and not any(r["mismatches"].values()) and r["index_underlyings_checked"] == r["index_rows"]]  # fmt: skip
    summary = {
        "days_compared": len(days),
        "days_identical": len(clean),
        "rows_compared": sum(r.get("rows", 0) for r in days.values()),
        "fields_compared": [*NUMERIC, "UndrlygPric (index rows)", "TradDt"],
        "columns_produced": list(COLUMNS),
        "problem_days": {d: r for d, r in days.items() if d not in clean},
    }
    (Path(__file__).with_name("overlap.json")).write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "columns_produced"}, indent=1))


if __name__ == "__main__":
    main()
