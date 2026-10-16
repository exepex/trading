"""Design 5.8's forecaster CUSUM on the v4 back-fill (exploratory, 2017-2026): d_t = Brier(forecaster) - Brier(base
rate) on V6a (2% move next session); s = SD of d over the first 60 scored outcomes; S = max(0, S + d/s - k), alarm
at S > h, restart at 0 after an alarm. Counts alarms; also the lag-1 autocorrelation of d."""
import csv, statistics, sys
from datetime import date
sys.path.insert(0, ".")
from fno.forecast_v4_rules import series
from fno.forecast_v4_rules.wiring import CLOSES_FILE

closes = series.regular_closes(series.closes_rows(CLOSES_FILE.read_text()))
outcomes = {o.day: o.value for o in series.big_move_outcomes(closes, 1)}

def probs(name, q="v6_abs_move_2pct_next_session"):
    rows = csv.DictReader(open(f"research/forecasts/v4/{name}/{q}.csv"))
    return {date.fromisoformat(r["day"]): float(r["value"]) for r in rows if r["value"] not in ("", None)}

base = probs("base_rate")
for name in ("v6_ewma_t4", "weather_vix_v1", "weather_checklist_v0"):
    p = probs(name)
    days = sorted(d for d in p if d in base and d in outcomes)
    d = [(p[x] - outcomes[x]) ** 2 - (base[x] - outcomes[x]) ** 2 for x in days]
    s = statistics.stdev(d[:60])
    mean = statistics.mean(d)
    ac = statistics.correlation(d[:-1], d[1:])
    for k, h in ((0.5, 5), (0.5, 4)):
        S, alarms = 0.0, []
        for x, v in zip(days, d):
            S = max(0.0, S + v / s - k)
            if S > h:
                alarms.append(x.isoformat()); S = 0.0
        print(f"{name}: n={len(d)} {days[0]}..{days[-1]} mean d={mean:+.5f} (sd first60 {s:.4f}, sd all {statistics.stdev(d):.4f}) lag1 ac={ac:+.3f} | k={k} h={h}: {len(alarms)} alarms {alarms[:6]}")

print("\n-- 20-session block means; s = SD of block means over the whole back-fill (2019-2025 only for s) --")
for name in ("v6_ewma_t4", "weather_vix_v1", "weather_checklist_v0"):
    p = probs(name)
    days = sorted(x for x in p if x in base and x in outcomes)
    d = [(p[x] - outcomes[x]) ** 2 - (base[x] - outcomes[x]) ** 2 for x in days]
    blocks = [(days[i], statistics.mean(d[i:i + 20])) for i in range(0, len(d) - 19, 20)]
    s = statistics.stdev([m for x, m in blocks if x.year <= 2025])
    ac = statistics.correlation([m for _, m in blocks][:-1], [m for _, m in blocks][1:])
    for k, h in ((0.5, 4), (0.5, 5)):
        S, alarms = 0.0, []
        for x, m in blocks:
            S = max(0.0, S + m / s - k)
            if S > h:
                alarms.append(x.isoformat()); S = 0.0
        print(f"{name}: {len(blocks)} blocks, mean block d={statistics.mean(m for _,m in blocks):+.5f}, s={s:.4f}, lag1 ac={ac:+.2f} | k={k} h={h}: {len(alarms)} alarms {alarms}")

import random
print("\n-- run length to alarm, resampling the real blocks (with replacement) plus a shift, 4,000 runs, seed 20261016 --")
rng = random.Random(20261016)
for name in ("v6_ewma_t4", "weather_vix_v1"):
    p = probs(name)
    days = sorted(x for x in p if x in base and x in outcomes)
    d = [(p[x] - outcomes[x]) ** 2 - (base[x] - outcomes[x]) ** 2 for x in days]
    blocks = [statistics.mean(d[i:i + 20]) for i in range(0, len(d) - 19, 20)]
    s = statistics.stdev(blocks[:-5])
    mu0 = statistics.mean(blocks)
    for h in (4, 5):
        out = []
        for label, shift in (("in control (its own record)", 0.0), ("edge gone (mean 0)", -mu0), ("worse than baseline by 0.5 s", -mu0 + 0.5 * s), ("by 1 s", -mu0 + s)):
            runs = []
            for _ in range(4000):
                S, t = 0.0, 0
                while t < 5000:
                    t += 1
                    S = max(0.0, S + (rng.choice(blocks) + shift) / s - 0.5)
                    if S > h: break
                runs.append(t)
            runs.sort()
            out.append(f"{label}: median {runs[2000]} blocks, mean {statistics.mean(runs):.0f}")
        print(f"{name} h={h}: " + " | ".join(out))
