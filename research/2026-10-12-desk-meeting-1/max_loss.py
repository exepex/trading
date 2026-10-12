"""Maximum possible loss per lot of meeting 1's condor variants, per cycle (correction of 12 Oct 2026).

Run from the repository root:  python research/2026-10-12-desk-meeting-1/max_loss.py   (writes max_loss.json)
Maximum loss = (wing width - credit) x lot, at entry prices (traded close, else settlement), before charges.
A negative value means a credit larger than the width: impossible in a real market (stale prices).
"""

from __future__ import annotations

import csv
import gzip
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import desk  # noqa: E402
import variants  # noqa: E402

CAP = 10_000


def main():
    spot, legs, monthly = desk.load()
    settle = defaultdict(dict)
    with gzip.open(desk.DATA / "nifty_options.csv.gz", "rt") as f:
        for r in csv.DictReader(f):
            if float(r["SttlmPric"]) > 0:
                settle[(r["TradDt"], r["XpryDt"])][(float(r["StrkPric"]), r["OptnTp"])] = float(r["SttlmPric"])
    out = {}
    for name, build in variants.VARIANTS.items():
        if "condor" not in name:
            continue
        losses = []
        for d, _x, e in desk.cycles(spot, legs, monthly):
            qty = build(sorted({k for k, _ in settle[(d, e)]}), spot[d])
            price = {leg: legs.get((d, e), {}).get(leg) or settle[(d, e)].get(leg) for leg in qty}
            if None in price.values():
                continue
            credit = sum(-q * price[leg] for leg, q in qty.items())
            calls = sorted(k for (k, t) in qty if t == "CE")
            puts = sorted(k for (k, t) in qty if t == "PE")
            losses.append(round((max(calls[1] - calls[0], puts[1] - puts[0]) - credit) * desk.LOT))
        out[name] = {
            "cycles": len(losses),
            "median": round(st.median(losses)),
            "min": min(losses),
            "max": max(losses),
            "within_cap": sum(x <= CAP for x in losses),
            "impossible_credit": sum(x < 0 for x in losses),
        }
    (HERE / "max_loss.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
