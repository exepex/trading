"""BR1 sizing: cross-underlying correlation of a frequent target, from NSE's UDiFF F&O bhavcopies.

Per session t and underlying u: spot S (UndrlygPric), the nearest expiry with >= 3 sessions left, the ATM straddle
(CE + PE close at the strike nearest S, both traded), implied daily move m = straddle / (S * sqrt(2/pi) * sqrt(n)).
Target Y(u,t) = 1 if |ln(S(t+1)/S(t))| >= m (next move beats the implied 1-sigma daily move).
Two forecasters: the market (p = 2*(1-Phi(1)) = 0.3173 if implied were right) and a 60-session trailing frequency.
Outputs the base rate, the average pairwise correlation of Y and of the Brier difference across underlyings
(day by day), the effective breadth N/(1+(N-1)rho), and the score-difference spread."""

import csv
import io
import math
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

RAW = Path(sys.argv[1])
MIN_SESSIONS_LEFT = 3


def read(path):
    with zipfile.ZipFile(path) as z:
        return list(csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8")))


days = sorted(p.stem for p in RAW.glob("*.zip"))
day_index = {d: i for i, d in enumerate(days)}
spot = defaultdict(dict)  # u -> day -> S
implied = defaultdict(dict)  # u -> day -> daily implied move
kind = {}
for d in days:
    rows = read(RAW / f"{d}.zip")
    chains = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))  # u -> expiry -> strike -> {CE, PE}
    for r in rows:
        tp = r["FinInstrmTp"]
        if tp not in ("STO", "IDO"):
            continue
        u = r["TckrSymb"]
        kind[u] = "index" if tp == "IDO" else "stock"
        s = float(r["UndrlygPric"] or 0)
        if s > 0:
            spot[u][d] = s
        if int(float(r["TtlTradgVol"] or 0)) > 0 and float(r["ClsPric"] or 0) > 0:
            chains[u][r["XpryDt"]][float(r["StrkPric"])][r["OptnTp"]] = float(r["ClsPric"])
    for u, by_expiry in chains.items():
        s = spot[u].get(d)
        if not s:
            continue
        for expiry in sorted(by_expiry):
            n = int(np.busday_count(d, expiry))  # weekdays to expiry (holidays ignored: sizing only)
            if n < MIN_SESSIONS_LEFT:
                continue
            strikes = [k for k, v in by_expiry[expiry].items() if "CE" in v and "PE" in v]
            if not strikes:
                break
            k = min(strikes, key=lambda x: abs(x - s))
            if abs(k - s) / s > 0.02:
                break
            straddle = by_expiry[expiry][k]["CE"] + by_expiry[expiry][k]["PE"]
            implied[u][d] = straddle / (s * math.sqrt(2 / math.pi) * math.sqrt(n))
            break

P_MARKET = 2 * (1 - 0.5 * (1 + math.erf(1 / math.sqrt(2))))
ys, d_brier = defaultdict(dict), defaultdict(dict)
for u in implied:
    hist = []
    for d in days[:-1]:
        nxt = days[day_index[d] + 1]
        if d in implied[u] and d in spot[u] and nxt in spot[u]:
            y = int(abs(math.log(spot[u][nxt] / spot[u][d])) >= implied[u][d])
            if len(hist) >= 60:
                p_trail = sum(hist[-60:]) / 60
                ys[u][d] = y
                d_brier[u][d] = (P_MARKET - y) ** 2 - (p_trail - y) ** 2
            hist.append(y)

units = [u for u in ys if len(ys[u]) >= 0.8 * max(len(v) for v in ys.values())]
cols = sorted({d for u in units for d in ys[u]})


def matrix(values):
    m = np.full((len(cols), len(units)), np.nan)
    for j, u in enumerate(units):
        for i, d in enumerate(cols):
            m[i, j] = values[u].get(d, np.nan)
    return m


def avg_corr(m):
    """Average pairwise correlation across columns (pairwise complete)."""
    df = np.ma.masked_invalid(m)
    c = np.ma.corrcoef(df, rowvar=False).filled(np.nan)
    iu = np.triu_indices(c.shape[0], 1)
    return float(np.nanmean(c[iu]))


def breadth(n, rho):
    return n / (1 + (n - 1) * rho)


Y, D = matrix(ys), matrix(d_brier)
idx = [j for j, u in enumerate(units) if kind[u] == "index"]
print(f"sessions {len(days)}, scored days {len(cols)}, underlyings {len(units)} ({len(idx)} indices)")
print(f"base rate of Y: {np.nanmean(Y):.3f} (market-implied would be {P_MARKET:.3f})")
for name, m in (("Y", Y), ("Brier difference", D)):
    rho_all = avg_corr(m)
    rho_idx = avg_corr(m[:, idx]) if len(idx) > 1 else float("nan")
    print(f"{name}: avg pairwise rho all {rho_all:.3f} -> N_eff {breadth(len(units), rho_all):.1f} of {len(units)};"
          f" indices {rho_idx:.3f} -> N_eff {breadth(len(idx), rho_idx):.2f} of {len(idx)}")
day_mean = np.nanmean(Y, axis=1)
print(f"share of Y variance from the day's market-wide mean: {np.nanvar(day_mean) / np.nanvar(Y):.3f}")
print(f"Brier difference: mean {np.nanmean(D):+.4f}, sd per (u,t) {np.nanstd(D):.4f},"
      f" sd of daily cross-sectional mean {np.nanstd(np.nanmean(D, axis=1)):.4f}")
lag1 = np.corrcoef(np.nanmean(D, axis=1)[:-1], np.nanmean(D, axis=1)[1:])[0, 1]
print(f"lag-1 autocorrelation of the daily mean Brier difference: {lag1:.3f}")
rets = defaultdict(dict)
for u in units:
    for d in cols:
        nxt = days[day_index[d] + 1]
        if d in spot[u] and nxt in spot[u]:
            rets[u][d] = math.log(spot[u][nxt] / spot[u][d])
R = matrix(rets)
rho_r = avg_corr(R)
print(f"signed next-day returns: avg pairwise rho {rho_r:.3f} -> N_eff {breadth(len(units), rho_r):.1f}")
print("indices:", [units[j] for j in idx])
