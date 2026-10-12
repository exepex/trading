"""Desk meeting 1: what 2024-2026 NIFTY data says, read by each expert role. Real NSE closing prices, real charges.

Run from the repository root:  python research/2026-10-12-desk-meeting-1/desk.py   (writes results.json)
Uses research/2026-10-12-capacity-screen/data (NSE daily files: NIFTY spot and option closes, 20-55 days to expiry).
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import statistics as st
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "2026-10-12-capacity-screen"))

from expiries import monthly_as_of  # noqa: E402

from fno.analytics import bs_price  # noqa: E402
from fno.config import load_config  # noqa: E402
from fno.costs import order_charges  # noqa: E402

DATA = ROOT / "research" / "2026-10-12-capacity-screen" / "data"
CHARGES = load_config(ROOT / "research" / "2026-10-12-backtest" / "inputs" / "config.yaml")["charges"]
LOT, RATE, PAD = 65, 0.065, 1.0  # current NIFTY lot; rate as the option model; Rs 1 adverse fill per leg per order
ENTRY_DTE, EXIT_DTE = (30, 45), 21  # enter a monthly 30-45 days out, close at the last close with >= 21 days left


def load():
    spot, legs = {}, defaultdict(dict)
    with gzip.open(DATA / "nifty_options.csv.gz", "rt") as f:
        for r in csv.DictReader(f):
            spot[r["TradDt"]] = float(r["UndrlygPric"])
            if float(r["ClsPric"]) > 0 and float(r["TtlTradgVol"]) > 0:
                legs[(r["TradDt"], r["XpryDt"])][(float(r["StrkPric"]), r["OptnTp"])] = float(r["ClsPric"])
    listings = defaultdict(dict)
    with gzip.open(DATA / "nifty_expiries.csv.gz", "rt") as f:
        for r in csv.DictReader(f):
            listings[date.fromisoformat(r["date"])][date.fromisoformat(r["expiry"])] = int(r["days_to_expiry"])
    monthly = {d.isoformat(): {e.isoformat() for e in known} for d, known in monthly_as_of(listings).items()}
    return spot, legs, monthly


def implied_vol(price, spot, strike, days, kind):
    lo, hi = 0.01, 2.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if bs_price(spot, strike, days / 365, RATE, mid, kind) > price:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def fee(price, side):
    return order_charges(max(price, 0.0), LOT, side, CHARGES)


def position_pnl(entry: dict, exit_: dict, qty: dict) -> float:
    """Net rupees for one lot of a multi-leg position. qty: +1 bought, -1 sold per (strike, kind)."""
    total = 0.0
    for leg, q in qty.items():
        e_px = entry[leg] + PAD if q > 0 else entry[leg] - PAD
        x_px = exit_[leg] - PAD if q > 0 else exit_[leg] + PAD
        total += q * (x_px - e_px) * LOT
        total -= fee(e_px, "buy" if q > 0 else "sell") + fee(x_px, "sell" if q > 0 else "buy")
    return total


def nearest(strikes, target):
    return min(strikes, key=lambda k: (abs(k - target), k))


def cycles(spot, legs, monthly_asof):
    """One entry per monthly expiry: the first day it is 30-45 days away (non-overlapping), and its exit day."""
    days = sorted(spot)
    out, used = [], set()
    for d in days:
        for e in sorted(monthly_asof.get(d, ())):
            dte = (date.fromisoformat(e) - date.fromisoformat(d)).days
            if ENTRY_DTE[0] <= dte <= ENTRY_DTE[1] and e not in used and (d, e) in legs:
                exits = [x for x in days if x > d and (date.fromisoformat(e) - date.fromisoformat(x)).days >= EXIT_DTE]
                exits = [x for x in exits if (x, e) in legs]
                if exits:
                    used.add(e)
                    out.append((d, exits[-1], e))
    return out


def realised_vol(spot, start, end):
    days = [d for d in sorted(spot) if start <= d <= end]
    r = [math.log(spot[b] / spot[a]) for a, b in zip(days, days[1:], strict=False)]
    return st.pstdev(r) * math.sqrt(252) if len(r) > 2 else None


def market_study(spot):
    days = sorted(spot)
    px = [spot[d] for d in days]
    rets = [math.log(b / a) for a, b in zip(px, px[1:], strict=False)]
    out = {
        "days": len(days),
        "nifty_change_pct": round((px[-1] / px[0] - 1) * 100, 1),
        "annual_vol_pct": round(st.pstdev(rets) * math.sqrt(252) * 100, 1),
        "worst_day_pct": round(min(rets) * 100, 2),
        "best_day_pct": round(max(rets) * 100, 2),
        "days_beyond_2pct": sum(abs(r) > 0.02 for r in rets),
    }
    for n in (5, 10, 20):  # does the last n days' move continue over the next n days? (non-overlapping blocks)
        blocks = [math.log(px[i + n] / px[i]) for i in range(0, len(px) - n, n)]
        pairs = list(zip(blocks, blocks[1:], strict=False))
        same = sum((a > 0) == (b > 0) for a, b in pairs)
        corr = st.correlation([a for a, _ in pairs], [b for _, b in pairs])
        out[f"trend_{n}d"] = {"pairs": len(pairs), "same_direction_pct": round(100 * same / len(pairs)),
                              "correlation": round(corr, 2)}  # fmt: skip
    return out


def trades(spot, legs, monthly_asof):
    rows = []
    for d, x, e in cycles(spot, legs, monthly_asof):
        s0, s1 = spot[d], spot[x]
        a, b = legs[(d, e)], legs[(x, e)]
        dte = (date.fromisoformat(e) - date.fromisoformat(d)).days
        strikes = sorted({k for k, _ in a})
        atm = nearest(strikes, s0)
        row = {"entry": d, "exit": x, "expiry": e, "dte": dte, "spot_in": s0, "spot_out": s1,
               "move_pct": round((s1 / s0 - 1) * 100, 2)}  # fmt: skip
        if (atm, "CE") in a and (atm, "PE") in a:
            iv = (implied_vol(a[(atm, "CE")], s0, atm, dte, "CE") + implied_vol(a[(atm, "PE")], s0, atm, dte, "PE")) / 2
            row["atm_iv_pct"] = round(iv * 100, 1)
            rv = realised_vol(spot, d, x)
            row["realised_vol_pct"] = round(rv * 100, 1) if rv else None
        plans = {
            "short_straddle": {(atm, "CE"): -1, (atm, "PE"): -1},
            "long_straddle": {(atm, "CE"): 1, (atm, "PE"): 1},
            "iron_condor_3_6pct": {
                (nearest(strikes, s0 * 1.03), "CE"): -1, (nearest(strikes, s0 * 1.06), "CE"): 1,
                (nearest(strikes, s0 * 0.97), "PE"): -1, (nearest(strikes, s0 * 0.94), "PE"): 1,
            },
            "bull_call_100": {(atm, "CE"): 1, (atm + 100, "CE"): -1},
            "bear_put_100": {(atm, "PE"): 1, (atm - 100, "PE"): -1},
        }  # fmt: skip
        for name, qty in plans.items():
            if all(leg in a and leg in b for leg in qty):
                row[name] = round(position_pnl(a, b, qty))
                if name == "iron_condor_3_6pct":
                    credit = sum(-q * a[leg] for leg, q in qty.items())
                    calls = sorted(k for (k, t), q in qty.items() if t == "CE")
                    puts = sorted(k for (k, t), q in qty.items() if t == "PE")
                    width = max(calls[1] - calls[0], puts[1] - puts[0])
                    row["condor_max_loss"] = round((width - credit) * LOT)
        rows.append(row)
    return rows


def summarise(rows, key):
    vals = [r[key] for r in rows if key in r]
    if not vals:
        return None
    run, worst_run = 0, 0
    for v in vals:
        run = run + v if v < 0 else 0
        worst_run = min(worst_run, run)
    return {"trades": len(vals), "net_total": round(sum(vals)), "avg": round(st.mean(vals)),
            "win_pct": round(100 * sum(v > 0 for v in vals) / len(vals)), "worst_trade": round(min(vals)),
            "best_trade": round(max(vals)), "worst_losing_run": round(worst_run)}  # fmt: skip


def main():
    spot, legs, monthly_asof = load()
    rows = trades(spot, legs, monthly_asof)
    vol = [r for r in rows if r.get("atm_iv_pct") and r.get("realised_vol_pct")]
    trend = [r for r in rows if "bull_call_100" in r and "bear_put_100" in r]
    sma20 = {}
    days = sorted(spot)
    for i, d in enumerate(days):
        if i >= 20:
            sma20[d] = st.mean(spot[x] for x in days[i - 20 : i])
    trend_follow = []
    for r in trend:
        if r["entry"] in sma20:
            up = r["spot_in"] > sma20[r["entry"]]
            trend_follow.append({"pnl": r["bull_call_100"] if up else r["bear_put_100"]})
    out = {
        "market": market_study(spot),
        "cycles": len(rows),
        "volatility": {
            "cycles": len(vol),
            "avg_implied_pct": round(st.mean(r["atm_iv_pct"] for r in vol), 1),
            "avg_realised_pct": round(st.mean(r["realised_vol_pct"] for r in vol), 1),
            "implied_above_realised_pct": round(
                100 * sum(r["atm_iv_pct"] > r["realised_vol_pct"] for r in vol) / len(vol)
            ),
        },
        "strategies": {
            k: summarise(rows, k)
            for k in ("short_straddle", "long_straddle", "iron_condor_3_6pct", "bull_call_100", "bear_put_100")
        },  # fmt: skip
        "trend_following_spread_100": summarise([{"x": t["pnl"]} for t in trend_follow], "x"),
        "condor_max_loss_median": round(st.median(r["condor_max_loss"] for r in rows if "condor_max_loss" in r)),
        "trades": rows,
    }
    (Path(__file__).parent / "results.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "trades"}, indent=1))


if __name__ == "__main__":
    main()
