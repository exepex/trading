"""Step 2 of the BR1 sizing: how independent are daily forecasts across F&O underlyings, and how many months does a
real skill take to show? Reads `extract.py`'s table.

Target `Y(u, t)` = 1 when `|ln(S(t+1) / S(t))|` is at least the implied daily move of day t. Spot is not adjusted for
corporate actions, so a contract-adjustment day is excluded by a rule written before the data is scored: fewer than
half of a stock's listed strikes on t, for an expiry listed on both days, are still listed on t+1. NSE replaces every
strike of a stock on a split, bonus or demerger (KOTAKBANK 14 Jan 2026, TATAMOTORS 14 Oct 2025: 0% kept) and keeps
them on an ordinary crash (KAYNES 14 May 2026, POLICYBZR 24 Sep 2026: 100% kept).

Forecasters, each from outcomes resolved before day t (an end-of-day forecast is made after t's close):
- `market`: p = 2(1 - Phi(1)) = 0.3173, the implied move taken at face value;
- `trail60`: the share of Y over the last 60 outcomes;
- `cal20`, `cal60`: the implied move scaled by k = mean(|r| / m) / sqrt(2 / pi) over the last 20 (60) outcomes,
  p = 2(1 - Phi(1 / k));
- `tilt`: `cal60` with k x 1.15 (a forecaster uniformly more volatility-bullish than the baseline: a regime call).

For each (baseline, forecaster) pair: d = Brier(baseline) - Brier(forecaster) per underlying-day (d > 0: the
forecaster is better), its mean and t, the average pairwise correlation of d across underlyings, N_eff = N / (1 +
(N - 1) rho), the SD and lag-1 autocorrelation of the daily cross-sectional mean of d, and the months a 2% or 3% Brier
skill needs at 80% power, one-sided, for K tests at 0.05/K (one look) and 0.02/K (v4's rate per look), with the
variance of the mean inflated by (1 + lag1) / (1 - lag1) for the day-to-day autocorrelation (AR(1)).

    python -I sizing.py <table.csv> [first day] [last day]
"""

import csv
import math
import sys
from collections import defaultdict
from statistics import NormalDist

import numpy as np

HISTORY, BIG_MOVE, TILT, COVERAGE, TOP, KEPT = 60, 0.15, 1.15, 0.8, 30, 0.5
P_MARKET = 2 * (1 - NormalDist().cdf(1))
HALF_NORMAL_MEAN = math.sqrt(2 / math.pi)
PAIRS = (("market", "trail60"), ("cal60", "trail60"), ("cal60", "cal20"), ("cal60", "tilt"))
SKILLS, FAMILIES, RATES = (0.02, 0.03), (3, 12), (0.05, 0.02)
SESSIONS_A_MONTH, POWER = 21, 0.8


def load(path, first, last):
    table = defaultdict(dict)
    with open(path) as f:
        for r in csv.DictReader(f):
            if first <= r["day"] <= last:
                table[r["underlying"]][r["day"]] = r
    return table


def strike_sets(text):
    return {e: set(ks.split(";")) for e, ks in (part.split("=") for part in text.split("|") if part)}


def adjusted(a, b):
    """True when NSE replaced most strikes between the two days (a contract adjustment)."""
    before, after = strike_sets(a["strikes"]), strike_sets(b["strikes"])
    common = sorted(set(before) & set(after))
    return bool(common) and len(before[common[0]] & after[common[0]]) < KEPT * len(before[common[0]])


def outcomes(rows, sessions):
    """day -> (y, |r| / m) for one underlying; None on a contract-adjustment day."""
    out, big = {}, 0
    for t, nxt in zip(sessions, sessions[1:], strict=False):
        a, b = rows.get(t), rows.get(nxt)
        if not (a and b and a["implied"]):
            continue
        if adjusted(a, b):
            out[t] = None
            continue
        r = abs(math.log(float(b["spot"]) / float(a["spot"])))
        big += r >= BIG_MOVE
        out[t] = (int(r >= float(a["implied"])), r / float(a["implied"]))
    return out, big


def p_calibrated(ratios, scale=1.0):
    k = scale * float(np.mean(ratios)) / HALF_NORMAL_MEAN
    return 2 * (1 - NormalDist().cdf(1 / k)) if k > 0 else 0.0


def forecasts(series):
    """day -> (y, {forecaster: p}), using only outcomes of earlier days."""
    days, out = sorted(d for d, v in series.items() if v is not None), {}
    for i, d in enumerate(days[HISTORY:], start=HISTORY):
        past = [series[x] for x in days[i - HISTORY : i]]
        ys, ratios = [y for y, _ in past], [q for _, q in past]
        out[d] = (series[d][0], {
            "market": P_MARKET, "trail60": sum(ys) / HISTORY, "cal20": p_calibrated(ratios[-20:]),
            "cal60": p_calibrated(ratios), "tilt": p_calibrated(ratios, TILT),
        })  # fmt: skip
    return out


def avg_corr(m):
    c = np.ma.corrcoef(np.ma.masked_invalid(m), rowvar=False).filled(np.nan)
    return float(np.nanmean(c[np.triu_indices(c.shape[0], 1)]))


def months(sd, lag1, skill, base_brier, k, rate):
    z = NormalDist().inv_cdf(1 - rate / k) + NormalDist().inv_cdf(POWER)
    inflation = (1 + lag1) / (1 - lag1) if lag1 > 0 else 1.0
    return (z * sd / (skill * base_brier)) ** 2 * inflation / SESSIONS_A_MONTH


def pair_report(name, scored, units, days):
    base, other = name
    d = np.full((len(days), len(units)), np.nan)
    brier = []
    for j, u in enumerate(units):
        for i, day in enumerate(days):
            if day in scored[u]:
                y, p = scored[u][day]
                d[i, j] = (p[base] - y) ** 2 - (p[other] - y) ** 2
                brier.append((p[base] - y) ** 2)
    daily = np.nanmean(d, axis=1)
    daily = daily[~np.isnan(daily)]
    sd, rho, b = float(np.std(daily)), avg_corr(d), float(np.mean(brier))
    t = float(np.mean(daily)) / (sd / math.sqrt(len(daily)))
    lag1 = float(np.corrcoef(daily[:-1], daily[1:])[0, 1])
    times = " ".join(f"{s:.0%}:" + "/".join(f"{months(sd, lag1, s, b, k, a):.1f}" for k in FAMILIES for a in RATES)
                     for s in SKILLS)  # fmt: skip
    print(
        f"  {base:>7} vs {other:<7} mean d {np.nanmean(d):+.4f} (t {t:+.2f}) rho_d {rho:.3f} "
        f"N_eff {len(units) / (1 + (len(units) - 1) * rho):5.1f} sd {sd:.4f} lag1 {lag1:+.3f} | {times}"
    )


def main(path, first="0000", last="9999"):
    table = load(path, first, last)
    sessions = sorted({d for rows in table.values() for d in rows})
    series, big = {}, 0
    for u, rows in table.items():
        series[u], b = outcomes(rows, sessions)
        big += b
    excluded = sum(v is None for s in series.values() for v in s.values())
    scored = {u: forecasts(s) for u, s in series.items()}
    longest = max(len(s) for s in scored.values())
    units = sorted(u for u in scored if len(scored[u]) >= COVERAGE * longest)
    days = sorted({d for u in units for d in scored[u]})
    turnover = {u: np.mean([float(r["turnover"]) for r in table[u].values()]) for u in units}
    top = sorted(units, key=turnover.get, reverse=True)[:TOP]
    ys = np.array([[scored[u].get(d, (np.nan,))[0] for u in units] for d in days], dtype=float)
    kinds = {u: next(iter(table[u].values()))["kind"] for u in units}
    print(
        f"window {sessions[0]} to {sessions[-1]}: {len(sessions)} sessions, {len(days)} scored days, "
        f"{len(units)} underlyings ({sum(kinds[u] == 'index' for u in units)} indices)"
    )
    print(f"contract-adjustment days excluded {excluded}; moves >= 15% left after the rule {big}")
    print(f"base rate of Y {np.nanmean(ys):.3f} (face-value implied {P_MARKET:.3f}); rho of Y {avg_corr(ys):.3f}")
    print("months columns: skill: K=3 a=.05 / K=3 a=.02 / K=12 a=.05 / K=12 a=.02")
    for label, chosen in (("all", units), (f"top {TOP} by option turnover", top),
                          ("indices", [u for u in units if kinds[u] == "index"])):  # fmt: skip
        print(f"{label} ({len(chosen)}):")
        for pair in PAIRS:
            pair_report(pair, scored, chosen, days)


if __name__ == "__main__":
    main(*sys.argv[1:])
