"""Desk meeting 2 (14 Oct 2026): first-strategy candidates for Book 1. Reproduces every number in
reviews/claude/response_92_first-strategy-candidates.md from data already in the repository. No new strategy P&L is
run on NSE option prices (that would be a new trial on spent data): sections 1-2 summarise experiment 1's recorded
results and features, 3-4 read the 14 Oct 15:00 quote snapshot, 5 measures NIFTY's own moves, 6 is a pricing model.

    python research/2026-10-14-desk-meeting-2/analysis.py
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import statistics as st
import sys
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "research/2026-10-12-experiment-1"
PANEL = ROOT / "research/data/nifty-panel"
SNAPSHOT = ROOT / "research/data/quotes/groww/derivatives/quote-snapshots/2026/10/nifty_20261014_145500.csv"
PERIODS = ("discovery", "challenge")
LOT = 65
NOV_EXPIRY, NOV_FUTURE, DAYS_TO_EXPIRY, EXIT_DAYS = "2026-11-23", 22760.0, 39.6, 21  # meta.json: Nov future last
PUT_SPREAD = {22000: (169.43, 0.1535), 21850: (141.60, 0.1550)}  # strike: (15:00 mid, implied vol), section 4
TWO_LEG_COST = 260 + 150  # pads Rs 1 x 2 legs x 2 sides x 65; charges about half a 4-leg SC's (experiment 1: ~235)
NORMAL = NormalDist().cdf
STRESS = 1.45  # risk.stressed_margin.multiplier (owner, 14 Oct)
EXPOSURE_PER_SHORT_LEG = 59077.07 / 2  # response 77: 2% x 22,721.95 x 65 per short leg (14 Oct NSE SPAN file)
SC300 = {
    "scan": 8517.60,
    "nov": -10153.00,
    "sold": [(23200, "CE"), (22250, "PE")],
    "bought": [(23500, "CE"), (21950, "PE")],
}
PUT_SPREAD_SCAN = (2650.70, 5423.60)  # no NSE row: bounded by the SC 100 and SC 200 rows' scan (one side's worst)


def opportunities(period: str) -> list[dict]:
    return json.loads((EXPERIMENT / f"results_{period}.json").read_text())["opportunities"]


def structure_stats() -> None:
    print("1. Experiment 1 per structure (traded, impossible exits removed), Rs per trade")
    for period in PERIODS:
        for code in ("SC", "SF", "BF"):
            rows = [o["structures"][code] for o in opportunities(period) if code in o["structures"]]
            clean = [r for r in rows if r["status"] == "traded" and not r["exit_outside_payoff"]]
            net = [r["net"] for r in clean]
            mean, sd = st.mean(net), st.stdev(net)
            proof = f"trades to prove this edge at 2 SE {(2 * sd / mean) ** 2:6.0f}" if mean > 0 else "no edge to prove"
            print(
                f"  {period:9} {code} n={len(net):2} gross {st.mean(r['gross'] for r in clean):6.0f} "
                f"costs {st.mean(r['charges'] + r['pads'] for r in clean):4.0f} net {mean:6.0f} sd {sd:5.0f} "
                f"worst {min(net):6.0f} {proof}"
            )
    edge, widest_sd = 153.0, 3403.0  # the 2024-26 condor's edge with the 2019-23 condor's spread
    print(f"  a +{edge:.0f} edge with SD {widest_sd:.0f} needs {(2 * widest_sd / edge) ** 2:.0f} trades at 2 SE")


def premium_feature() -> None:
    print("2. F1 = ATM implied vol minus past 20-day realised, at entry (points)")
    for period in PERIODS:
        f1 = [o["features"]["F1_atm_iv_minus_rv20"] for o in opportunities(period)]
        f1 = [x for x in f1 if x is not None]
        share = 100 * sum(x > 0 for x in f1) / len(f1)
        print(f"  {period:9} n {len(f1)} mean {st.mean(f1):.2f} median {st.median(f1):.2f} above 0 {share:.0f}%")


def november_quotes() -> list[dict]:
    rows = csv.DictReader(SNAPSHOT.open(encoding="utf-8"))
    return [r for r in rows if r["expiry"] == NOV_EXPIRY and r["valid"] == "true"]


def black76(forward: float, strike: float, years: float, vol: float, kind: str) -> float:
    d1 = (math.log(forward / strike) + vol * vol * years / 2) / (vol * math.sqrt(years))
    d2 = d1 - vol * math.sqrt(years)
    if kind == "CE":
        return forward * NORMAL(d1) - strike * NORMAL(d2)
    return strike * NORMAL(-d2) - forward * NORMAL(-d1)


def implied_vol(forward: float, strike: float, years: float, price: float, kind: str) -> float:
    low, high = 0.01, 2.0
    for _ in range(100):
        middle = (low + high) / 2
        low, high = (low, middle) if black76(forward, strike, years, middle, kind) > price else (middle, high)
    return (low + high) / 2


def spreads_and_skew() -> None:
    print(f"3-4. 14 Oct 14:55 IST quotes, {NOV_EXPIRY} expiry: out-of-the-money half-spread and implied vol")
    years = DAYS_TO_EXPIRY / 365
    for r in sorted(november_quotes(), key=lambda r: float(r["strike"])):
        strike, kind = float(r["strike"]), r["type"]
        out_of_the_money = (kind == "PE" and strike <= NOV_FUTURE) or (kind == "CE" and strike >= NOV_FUTURE)
        if not out_of_the_money or abs(strike / NOV_FUTURE - 1) > 0.06 or strike % 100:
            continue
        bid, ask = float(r["bid"]), float(r["ask"])
        vol = implied_vol(NOV_FUTURE, strike, years, (bid + ask) / 2, kind)
        moneyness = (strike / NOV_FUTURE - 1) * 100
        print(f"  {kind} {strike:7.0f} {moneyness:+5.1f}% half-spread {(ask - bid) / 2:5.2f} IV {vol * 100:5.2f}%")


def underlying_by_day() -> dict[str, float]:
    closes = {}
    for year in range(2019, 2027):
        with gzip.open(PANEL / f"futures_{year}.csv.gz", "rt") as f:
            closes.update({r["date"]: float(r["underlying"]) for r in csv.DictReader(f) if r["underlying"]})
    return closes


def holding_moves(closes: dict[str, float], to_expiry: bool = False) -> list[float]:
    days = sorted(closes)
    moves = []
    for period in PERIODS:
        for o in opportunities(period):
            cycle = o["cycle"]
            end = cycle["expiry"] if to_expiry else cycle["exit_day"]
            if cycle["entry_day"] not in closes or end > days[-1]:
                continue
            last = closes[max(d for d in days if d <= end)]
            moves.append(last / closes[cycle["entry_day"]] - 1)
    return moves


def market_moves(moves: list[float]) -> None:
    falls3, falls5 = sum(m <= -0.03 for m in moves), sum(m <= -0.05 for m in moves)
    print(f"5. NIFTY over the {len(moves)} holding windows: fell 3%+ {falls3}, 5%+ {falls5}, worst {min(moves):.1%}")


def put_spread_model(closes: dict[str, float]) -> None:
    """Today's put-spread prices replayed on history's moves, implied vol fixed per strike (sticky strike)."""
    (short_strike, (short_mid, short_vol)), (long_strike, (long_mid, long_vol)) = PUT_SPREAD.items()
    credit = (short_mid - long_mid) * LOT
    width = short_strike - long_strike
    exit_years = EXIT_DAYS / 365
    cap = width * LOT - credit + TWO_LEG_COST
    print(f"6. Model: short {short_strike} / long {long_strike} put, credit {credit:.0f}, max loss {cap:.0f}")
    for bump in (0.0, 0.03):
        nets = []
        for move in holding_moves(closes):
            forward = NOV_FUTURE * (1 + move)
            extra = bump if move < -0.02 else 0.0
            value = black76(forward, short_strike, exit_years, short_vol + extra, "PE")
            value -= black76(forward, long_strike, exit_years, long_vol + extra, "PE")
            nets.append(credit - value * LOT - TWO_LEG_COST)
        label = "exit at 21 days" + (", +3 vol points in falls over 2%" if bump else "")
        wins = 100 * sum(n > 0 for n in nets) / len(nets)
        print(f"  {label}: mean {st.mean(nets):.0f} sd {st.stdev(nets):.0f} worst {min(nets):.0f} win {wins:.0f}%")
    settle_cost = TWO_LEG_COST - 130  # no exit pads when held to expiry
    expiry_nets = []
    for move in holding_moves(closes, to_expiry=True):
        loss = max(0.0, min(width, short_strike - NOV_FUTURE * (1 + move))) * LOT
        expiry_nets.append(credit - loss - settle_cost)
    wins = 100 * sum(n > 0 for n in expiry_nets) / len(expiry_nets)
    print(f"  held to expiry: mean {st.mean(expiry_nets):.0f} worst {min(expiry_nets):.0f} win {wins:.0f}%")


def funds_at_entry() -> None:
    """C2's stressed margin and funds at entry (fno/risk/margins.py; judge 77 addendum 3): the broker credits no sold
    premium at entry and takes the bought premium at once."""
    sys.path.insert(0, str(ROOT))
    import yaml

    from fno.costs import order_charges

    charges = yaml.safe_load((ROOT / "config.yaml").read_text())["charges"]
    quotes = {(float(r["strike"]), r["type"]): r for r in november_quotes()}

    def entry(sold, bought):
        paid = sum(float(quotes[leg]["ask"]) * LOT for leg in bought)
        received = sum(float(quotes[leg]["bid"]) * LOT for leg in sold)
        fees = sum(order_charges(float(quotes[leg]["ask"]), LOT, "buy", charges) for leg in bought)
        fees += sum(order_charges(float(quotes[leg]["bid"]), LOT, "sell", charges) for leg in sold)
        return paid, received, fees

    print("7. Per lot, 14 Oct: C2 stressed margin = max(0, k x scan - NOV) + min(0, NOV) + exposure;")
    print("   funds at entry = max(0, k x scan - NOV) + exposure + bought premium + entry charges")
    paid, received, fees = entry(SC300["sold"], SC300["bought"])
    no_credit = max(0.0, STRESS * SC300["scan"] - SC300["nov"]) + 2 * EXPOSURE_PER_SHORT_LEG
    margin = no_credit + min(0.0, SC300["nov"])
    print(
        f"  SC 300: stressed margin {margin:.0f}; funds {no_credit + paid + fees:.0f}"
        f" (bought {paid:.0f}, fees {fees:.0f})"
    )
    paid, received, fees = entry([(22000, "PE")], [(21850, "PE")])
    nov = paid - received  # the legs' value at today's fills (NSE's file uses settlement prices)
    for scan in PUT_SPREAD_SCAN:
        no_credit = max(0.0, STRESS * scan - nov) + EXPOSURE_PER_SHORT_LEG
        margin = no_credit + min(0.0, nov)
        print(
            f"  put spread 22000/21850, scan {scan:.0f}: stressed margin {margin:.0f};"
            f" funds {no_credit + paid + fees:.0f}"
        )


if __name__ == "__main__":
    structure_stats()
    premium_feature()
    spreads_and_skew()
    closes = underlying_by_day()
    market_moves(holding_moves(closes))
    put_spread_model(closes)
    funds_at_entry()
