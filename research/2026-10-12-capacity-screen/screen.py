"""Capacity screen: on each trading day, would a NIFTY debit spread have fitted the risk cap? No strategy, no P&L.

Run from the repository root after fetch.py:  python research/2026-10-12-capacity-screen/screen.py
Scope (agreed in ChatGPT review 4):
- the monthly NIFTY expiry with 30-45 calendar days left; an expiry is monthly once NSE has listed it more than 50
  days ahead (expiries.monthly_as_of, from the stored expiry lists, as of each day), never from the filtered prices;
- nearest listed strike; bull call and bear put spreads 50/100/200 points wide;
- daily closing prices (not executable quotes); today's lot size and charges (a labelled counterfactual quantity
  for old dates); a one-way adverse pad per leg per order.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from expiries import eligible_monthly, monthly_as_of  # noqa: E402

from fno.config import load_config  # noqa: E402
from fno.costs import order_charges  # noqa: E402

HERE = Path(__file__).resolve().parent
CONFIG = ROOT / "research" / "2026-10-12-backtest" / "inputs" / "config.yaml"
CONFIG_SHA256 = "cc6d55bde201034b475cb9a29067e98750d352b9724c8a0d226734d31be14742"
CURRENT_LOT = 65  # NIFTY lot from January 2026 (frozen config `lot_sizes`)
WIDTHS = (50, 100, 200)
PADS = (0.0, 0.5, 1.0, 2.0)  # rupees per leg per executed order, one way and adverse
PROFILES = {"2L_1pct": 2000.0, "2L_2pct": 4000.0, "5L_1pct": 5000.0}
REFERENCE = "2L_1pct"
DIRECTIONS = {"bull_call": ("CE", 1), "bear_put": ("PE", -1)}
SCREEN_FIELDS = [
    "date", "direction", "width", "pad", "status", "expiry", "days_to_expiry", "spot", "long_strike", "short_strike",
    "spot_minus_long_strike", "historical_lot", "long_close", "short_close", "debit_points", "admission",
    *(f"fits_{name}" for name in PROFILES),
]  # fmt: skip


def nearest_strike(spot: float, strikes: list[float]) -> float:
    """Nearest listed strike; a tie goes to the lower strike."""
    return min(strikes, key=lambda k: (abs(k - spot), k))


def admission(long_price: float, short_price: float, pad: float, lot: int, charges: dict) -> float:
    """Rupees reserved to admit the spread: padded entry debit, entry charges on padded prices, an exit-charge
    reserve at the entry prices padded adversely, and the remaining exit pads (2 x pad x lot). In total the four
    orders carry 4 x pad x lot of price padding, counted once."""
    fee = lambda price, side: order_charges(max(price, 0.0), lot, side, charges)  # noqa: E731
    debit = (long_price - short_price + 2 * pad) * lot
    entry_fees = fee(long_price + pad, "buy") + fee(short_price - pad, "sell")
    exit_reserve = fee(long_price - pad, "sell") + fee(short_price + pad, "buy") + 2 * pad * lot
    return debit + entry_fees + exit_reserve


def leg_status(row: dict | None) -> str | None:
    if row is None:
        return "missing_required_leg"
    price = float(row["ClsPric"])
    if not price > 0:
        return "invalid_price"
    if float(row["TtlTradgVol"]) <= 0:
        return "zero_volume_price_unusable"
    return None


def screen_day(day: date, rows: list[dict], monthly: set[date], charges: dict) -> list[dict]:
    """`monthly`: the monthly expiries listed that day (from the complete file), never inferred from `rows`."""
    expiry = eligible_monthly(day, monthly)
    out = []
    for direction, (kind, sign) in DIRECTIONS.items():
        for width in WIDTHS:
            base = {"date": day.isoformat(), "direction": direction, "width": width}
            if expiry is None:
                out += [{**base, "pad": p, "status": "no_eligible_expiry"} for p in PADS]
                continue
            legs = {float(r["StrkPric"]): r for r in rows if r["XpryDt"] == expiry.isoformat() and r["OptnTp"] == kind}
            spot = float(rows[0]["UndrlygPric"])
            if not legs:
                out += [{**base, "pad": p, "status": "contract_unavailable"} for p in PADS]
                continue
            long_strike = nearest_strike(spot, list(legs))
            short_strike = long_strike + sign * width
            long_row, short_row = legs.get(long_strike), legs.get(short_strike)
            status = leg_status(long_row) or leg_status(short_row)
            detail = {
                **base,
                "expiry": expiry.isoformat(),
                "days_to_expiry": (expiry - day).days,
                "spot": spot,
                "long_strike": long_strike,
                "short_strike": short_strike,
                "spot_minus_long_strike": round(spot - long_strike, 2),
                "historical_lot": long_row["NewBrdLotQty"] if long_row else "",
            }
            if status is None:
                long_price, short_price = float(long_row["ClsPric"]), float(short_row["ClsPric"])
                debit_points = long_price - short_price
                detail.update(long_close=long_price, short_close=short_price, debit_points=round(debit_points, 2))
                if not 0 < debit_points < width:
                    status = "nonsynchronous_price_anomaly"
            for pad in PADS:
                row = {**detail, "pad": pad}
                if status:
                    row["status"] = status
                else:
                    cost = admission(long_price, short_price, pad, CURRENT_LOT, charges)
                    row["admission"] = round(cost, 2)
                    row["status"] = "priced"
                    for name, cap in PROFILES.items():
                        row[f"fits_{name}"] = int(cost <= cap)
                out.append(row)
    return out


def main() -> None:
    if hashlib.sha256(CONFIG.read_bytes()).hexdigest() != CONFIG_SHA256:
        raise SystemExit("frozen config changed")
    charges = load_config(CONFIG)["charges"]
    by_day: dict[str, list[dict]] = defaultdict(list)
    with gzip.open(HERE / "data" / "nifty_options.csv.gz", "rt") as f:
        for row in csv.DictReader(f):
            by_day[row["TradDt"]].append(row)
    listings: dict[date, dict[date, int]] = defaultdict(dict)
    with gzip.open(HERE / "data" / "nifty_expiries.csv.gz", "rt") as f:
        for row in csv.DictReader(f):
            listings[date.fromisoformat(row["date"])][date.fromisoformat(row["expiry"])] = int(row["days_to_expiry"])
    monthly = {day.isoformat(): known for day, known in monthly_as_of(listings).items()}
    with open(HERE / "data" / "manifest.csv") as f:
        manifest = list(csv.DictReader(f))
    results = []
    for entry in manifest:
        if entry["status"] != "200":
            continue  # no file at that URL (not a certified holiday)
        if entry["date"] not in monthly:
            results.append({"date": entry["date"], "status": "expiry_list_unavailable"})
            continue
        rows = by_day.get(entry["date"])
        if not rows:
            results.append({"date": entry["date"], "status": "data_unavailable"})
            continue
        results += screen_day(date.fromisoformat(entry["date"]), rows, monthly[entry["date"]], charges)
    with open(HERE / "screen.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, SCREEN_FIELDS)  # a fixed order, so every run writes identical bytes
        writer.writeheader()
        writer.writerows(results)
    write_summary(manifest, results)


def write_summary(manifest: list[dict], results: list[dict]) -> None:
    trading_days = sum(e["status"] == "200" for e in manifest)
    lines = [
        "# Capacity screen results",
        "",
        f"Days with an NSE file: {trading_days} ({manifest[0]['date']} to {manifest[-1]['date']},"
        " every calendar day asked; file availability, not a certified exchange calendar).",
        "Counts are days. 'Admitted' means the spread's admission reserve fit the profile's cap at the day's closing",
        "prices; it is not evidence that the trade could have been executed at those prices.",
        "",
        "| Direction | Width | Pad Rs | Priced | No eligible expiry | Contract unavailable | Missing leg |"
        " Zero volume or bad price | Anomaly |"
        " Admitted 2L 1% (reference) | Admitted 2L 2% | Admitted 5L 1% |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    groups: dict[tuple, Counter] = defaultdict(Counter)
    for r in results:
        if "direction" not in r:
            continue
        g = groups[(r["direction"], r["width"], r["pad"])]
        g[r["status"]] += 1
        for name in PROFILES:
            g[name] += r.get(f"fits_{name}", 0)
    for (direction, width, pad), g in sorted(groups.items()):
        lines.append(
            f"| {direction} | {width} | {pad:.2f} | {g['priced']} | {g['no_eligible_expiry']} |"
            f" {g['contract_unavailable']} |"
            f" {g['missing_required_leg']} | {g['zero_volume_price_unusable'] + g['invalid_price']} |"
            f" {g['nonsynchronous_price_anomaly']} | {g['2L_1pct']} | {g['2L_2pct']} | {g['5L_1pct']} |"
        )
    unavailable = sum(r["status"] == "data_unavailable" for r in results)
    lines += ["", f"Trading days with a file but no usable NIFTY rows: {unavailable}."]
    (HERE / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
