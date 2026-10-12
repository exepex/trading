"""Protected premium-selling variants, with NSE settlement prices where an option did not trade that day (so no month
is dropped for a missing price). Run from the repository root; writes variants.json."""

from __future__ import annotations

import csv
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import desk  # noqa: E402

N = desk.nearest
VARIANTS = {
    "short_straddle": lambda s, s0: {(N(s, s0), "CE"): -1, (N(s, s0), "PE"): -1},
    **{
        f"condor_short_{int(sc * 100)}pct_wings_{wc}": (
            lambda s, s0, sc=sc, wc=wc: {
                (N(s, s0 * (1 + sc)), "CE"): -1, (N(s, s0 * (1 + sc)) + wc, "CE"): 1,
                (N(s, s0 * (1 - sc)), "PE"): -1, (N(s, s0 * (1 - sc)) - wc, "PE"): 1,
            }
        )
        for sc in (0.0, 0.02, 0.03)
        for wc in (300, 500)
    },
}  # fmt: skip


def main():
    spot, legs, monthly = desk.load()
    settle = defaultdict(dict)
    with gzip.open(desk.DATA / "nifty_options.csv.gz", "rt") as f:
        for r in csv.DictReader(f):
            if float(r["SttlmPric"]) > 0:
                settle[(r["TradDt"], r["XpryDt"])][(float(r["StrkPric"]), r["OptnTp"])] = float(r["SttlmPric"])
    cycles = desk.cycles(spot, legs, monthly)

    def price(day, expiry, leg):
        traded = legs.get((day, expiry), {}).get(leg)
        return (traded, False) if traded else (settle.get((day, expiry), {}).get(leg), True)

    out = {}
    for name, build in VARIANTS.items():
        trades, settled, missing = [], 0, []
        for d, x, e in cycles:
            qty = build(sorted({k for k, _ in settle[(d, e)]}), spot[d])
            a, b = {}, {}
            for leg in qty:
                (pa, sa), (pb, sb) = price(d, e, leg), price(x, e, leg)
                if pa is None or pb is None:
                    missing.append(d)
                    break
                a[leg], b[leg] = pa, pb
                settled += sa + sb
            else:
                trades.append({"entry": d, "exit": x, "move_pct": round((spot[x] / spot[d] - 1) * 100, 2),
                               "net": round(desk.position_pnl(a, b, qty))})  # fmt: skip
        nets = [t["net"] for t in trades]
        out[name] = {
            **desk.summarise([{"x": v} for v in nets], "x"),
            "cycles_available": f"{len(trades)}/{len(cycles)}",
            "legs_priced_at_settlement": settled,
            "months_missing_a_strike": missing,
            "trades": trades,
        }
    (Path(__file__).parent / "variants.json").write_text(json.dumps(out, indent=1) + "\n")
    for name, v in out.items():
        line = f"{name:32} {v['cycles_available']:>6} net {v['net_total']:>9,}"
        print(f"{line} win {v['win_pct']}% worst {v['worst_trade']:>8,}")


if __name__ == "__main__":
    main()
