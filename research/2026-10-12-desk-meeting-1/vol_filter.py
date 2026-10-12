"""Review 9 follow-up: does an entry-known volatility comparison separate good and bad short-volatility months?

Run from the repository root:  python research/2026-10-12-desk-meeting-1/vol_filter.py   (writes vol_filter.json)
Reads results.json (from desk.py) and the same NSE data. Exploratory: 2024-2026 is discovery data; every comparison
below is listed in research/LEDGER.md. The short straddle is a diagnostic only (unprotected, outside the owner's limit).
"""

from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import desk  # noqa: E402

PAST_DAYS = 20  # trailing realised volatility known at entry: the 20 daily returns ending on the entry close


def groups(rows, name, test):
    out = {}
    for label, keep in (("yes", True), ("no", False)):
        pnl = [r["short_straddle"] for r in rows if test(r) == keep]
        out[label] = {
            "cycles": len(pnl),
            "wins": sum(p > 0 for p in pnl),
            "net": sum(pnl),
            "worst": min(pnl, default=0),
        }
    return {"split": name, **out}


def main():
    spot, _, _ = desk.load()
    days = sorted(spot)
    rows = json.loads((HERE / "results.json").read_text())["trades"]
    rows = [
        r for r in rows if r.get("short_straddle") is not None and r.get("atm_iv_pct") and r.get("realised_vol_pct")
    ]
    for r in rows:
        last = max(d for d in days if d <= r["expiry"])
        start = days[max(0, days.index(r["entry"]) - PAST_DAYS)]
        r["rv_to_expiry_pct"] = round(desk.realised_vol(spot, r["entry"], last) * 100, 1)
        r["rv_past_pct"] = round(desk.realised_vol(spot, start, r["entry"]) * 100, 1)
    result = {
        "cycles": len(rows),
        "average_pct": {
            k: round(st.mean(r[k] for r in rows), 1)
            for k in ("atm_iv_pct", "realised_vol_pct", "rv_to_expiry_pct", "rv_past_pct")
        },  # fmt: skip
        "splits": [
            groups(rows, "hindsight: IV > realised over holding", lambda r: r["atm_iv_pct"] > r["realised_vol_pct"]),
            groups(rows, "hindsight: IV > realised entry to expiry", lambda r: r["atm_iv_pct"] > r["rv_to_expiry_pct"]),
            groups(rows, "entry-known: IV > past 20-day realised", lambda r: r["atm_iv_pct"] > r["rv_past_pct"]),
            groups(
                rows, "entry-known: IV > past 20-day realised + 2", lambda r: r["atm_iv_pct"] > r["rv_past_pct"] + 2
            ),
        ],
        "worst_cycles": [
            {k: r[k] for k in ("entry", "short_straddle", "atm_iv_pct", "rv_past_pct", "realised_vol_pct", "move_pct")}
            for r in sorted(rows, key=lambda r: r["short_straddle"])[:5]
        ],
    }
    (HERE / "vol_filter.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
