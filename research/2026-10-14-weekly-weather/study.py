"""Weekly NIFTY options and the market-weather signal: the frozen study (PROTOCOL.md in this folder).

    python research/2026-10-14-weekly-weather/study.py --check   # data and fill counts only: no P&L, no colours
    python research/2026-10-14-weekly-weather/study.py           # the one run: writes results.json and results.md

Research only. Reads the NIFTY panel, the warm-up closes and the event calendar; uses `fno.costs` for C1 charges.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import math
import statistics as st
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from fno.costs import order_charges, settlement_charges_breakdown  # noqa: E402

PANEL, YEARS = ROOT / "research/data/nifty-panel", range(2019, 2027)
CLOSES, EVENTS = PANEL / "warmup_closes.csv", ROOT / "research/data/events/events.csv"
LOT, PAD, CAP, WING, HIT = 65, 1.0, 10_000.0, 100.0, 0.9
STRUCTURES = ("W1", "W2", "W3", "W4", "W5")
T_PASS, WELCH_PASS, SEED, RESAMPLES = 2.33, 1.645, 20261014, 10_000
CRASH_2020 = (date(2020, 2, 17), date(2020, 4, 30))
CRASH_2024 = date(2024, 6, 4)


def read_closes() -> list[dict]:
    rows = list(csv.DictReader(CLOSES.open(encoding="utf-8")))
    return [{"day": date.fromisoformat(r["date"]), "session": r["session"], "close": float(r["underlying"]),
             "vix": float(r["vix"])} for r in rows]  # fmt: skip


def read_events() -> list[dict]:
    rows = csv.DictReader(EVENTS.open(encoding="utf-8"))
    return [{"day": date.fromisoformat(r["date"]), "announced": date.fromisoformat(r["announced_on"])}
            for r in rows if r["scheduled"] == "yes" and r["announced_on"]]  # fmt: skip


def expiries() -> list[date]:
    found = set()
    for year in YEARS:
        with gzip.open(PANEL / f"options_{year}.csv.gz", "rt") as f:
            found.update(r["expiry"] for r in csv.DictReader(f))
    return sorted(date.fromisoformat(e) for e in found)


def opportunities(closes: list[dict]) -> list[dict]:
    """One per expiry: entry on the first regular session after the previous expiry (PROTOCOL section 3)."""
    days = [c["day"] for c in closes]
    index = {d: i for i, d in enumerate(days)}
    found, listed = [], expiries()
    for previous, expiry in zip(listed, listed[1:]):
        after = [i for i, d in enumerate(days) if previous < d < expiry]
        if not after or expiry not in index:
            continue
        entry = after[0]
        if closes[entry]["session"] != "regular" or index[expiry] - entry < 2 or entry == 0:
            continue
        found.append({"expiry": expiry, "entry": days[entry], "decision": days[entry - 1], "entry_i": entry})
    return found


def chains(wanted: set[tuple[date, date]]) -> dict:
    """(entry day, expiry) -> {(strike, type): (close, volume)}, only for the opportunities' entry days."""
    out: dict = {}
    for year in YEARS:
        with gzip.open(PANEL / f"options_{year}.csv.gz", "rt") as f:
            for r in csv.DictReader(f):
                key = (date.fromisoformat(r["date"]), date.fromisoformat(r["expiry"]))
                if key in wanted:
                    out.setdefault(key, {})[(float(r["strike"]), r["type"])] = (float(r["close"]), int(r["volume"]))
    return out


def nearest(strikes: list[float], target: float) -> float:
    return min(strikes, key=lambda k: (abs(k - target), -k))


def legs(code: str, chain: dict, spot: float) -> list[tuple[float, str, int]] | None:
    """(strike, type, side) per leg: side +1 bought, -1 sold (PROTOCOL section 3 table)."""
    calls = sorted(k for k, t in chain if t == "CE")
    puts = sorted(k for k, t in chain if t == "PE")
    if not calls or not puts:
        return None
    if code == "W1":
        return [(nearest(calls, spot * 1.01), "CE", 1)]
    if code == "W2":
        return [(nearest(puts, spot * 0.99), "PE", 1)]
    if code == "W3":
        k = nearest(calls, spot)
        return [(k, "CE", 1), (k + WING, "CE", -1)]
    if code == "W4":
        k = nearest(puts, spot)
        return [(k, "PE", 1), (k - WING, "PE", -1)]
    call, put = nearest(calls, spot * 1.015), nearest(puts, spot * 0.985)
    return [(call, "CE", -1), (call + WING, "CE", 1), (put, "PE", -1), (put - WING, "PE", 1)]


def intrinsic(strike: float, kind: str, spot: float) -> float:
    return max(0.0, spot - strike) if kind == "CE" else max(0.0, strike - spot)


def trade(code: str, chain: dict, spot: float, settle: float, charges: dict) -> dict:
    """One structure's trade: status, net, maximum loss (all Rs, one lot)."""
    built = legs(code, chain, spot)
    if built is None or any((k, t) not in chain or chain[(k, t)][1] <= 0 for k, t, _ in built):
        return {"status": "unfillable"}
    fills = [(k, t, s, chain[(k, t)][0] + PAD * s) for k, t, s in built]
    entry_cash = -sum(s * price for _, _, s, price in fills) * LOT  # received minus paid
    entry_fees = sum(order_charges(price, LOT, "buy" if s > 0 else "sell", charges) for _, _, s, price in fills)
    worst_payoff = min(sum(s * intrinsic(k, t, x) for k, t, s, _ in fills) for x in (0.0, 1e9, *[k for k, *_ in fills]))
    max_loss = -(entry_cash + worst_payoff * LOT) + entry_fees
    if max_loss > CAP:
        return {"status": "over_cap", "max_loss": max_loss}
    payoff = sum(s * intrinsic(k, t, settle) for k, t, s, _ in fills) * LOT
    exit_fees = sum(sum(settlement_charges_breakdown(intrinsic(k, t, settle), LOT, "sell" if s > 0 else "buy",
                                                     charges).values()) for k, t, s, _ in fills)  # fmt: skip
    gross = entry_cash + payoff
    return {"status": "traded", "gross": gross, "costs": entry_fees + exit_fees, "net": gross - entry_fees - exit_fees,
            "max_loss": max_loss}  # fmt: skip


def weather(closes: list[dict], i: int, entry: date, expiry: date, events: list[dict]) -> str:
    """The colour on decision day index i (PROTOCOL section 5)."""
    vix = closes[i]["vix"]
    vix_ratio = vix / st.median(c["vix"] for c in closes[i - 250 : i])
    vix_change5 = vix / closes[i - 5]["vix"] - 1
    returns = [math.log(closes[j]["close"] / closes[j - 1]["close"]) for j in range(i - 9, i + 1)]
    move5 = max(abs(closes[j]["close"] / closes[j - 1]["close"] - 1) for j in range(i - 4, i + 1))
    rv10 = math.sqrt(252 * sum(r * r for r in returns) / len(returns))
    day = closes[i]["day"]
    event = any(e["announced"] <= day and entry < e["day"] <= expiry for e in events)
    if vix_ratio >= 1.30 or vix_change5 >= 0.20 or move5 >= 0.020 or rv10 >= 0.25:
        return "RED"
    if vix_ratio >= 1.10 or vix_change5 >= 0.10 or move5 >= 0.0125 or rv10 >= 0.18 or event:
        return "AMBER"
    return "GREEN"


def build_trades(check: bool) -> list[dict]:
    closes, events = read_closes(), read_events()
    charges = yaml.safe_load((ROOT / "config.yaml").read_text())["charges"]
    by_day = {c["day"]: c for c in closes}
    opps = opportunities(closes)
    books = chains({(o["entry"], o["expiry"]) for o in opps})
    out = []
    for o in opps:
        chain = books.get((o["entry"], o["expiry"]), {})
        spot, settle = by_day[o["entry"]]["close"], by_day[o["expiry"]]["close"]
        row = {"entry": o["entry"].isoformat(), "expiry": o["expiry"].isoformat(), "spot": spot}
        row["trades"] = {code: trade(code, chain, spot, settle, charges) for code in STRUCTURES}
        if not check:
            row["weather"] = weather(closes, o["entry_i"] - 1, o["entry"], o["expiry"], events)
        out.append(row)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="counts only: no P&L and no colours are printed")
    args = parser.parse_args()
    rows = build_trades(args.check)
    if args.check:
        print(f"opportunities {len(rows)}, first entry {rows[0]['entry']}, last expiry {rows[-1]['expiry']}")
        for code in STRUCTURES:
            statuses = [r["trades"][code]["status"] for r in rows]
            print(code, {s: statuses.count(s) for s in sorted(set(statuses))})
        sys.exit(0)
    from report import write_report  # the frozen report module, next to this file

    write_report(rows, HERE)
