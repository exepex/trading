"""LR3's proposed calibration on experiment 1's real nets: the smallest h (steps of 0.5) whose in-control median run
length, by resampling the version's own per-trade nets (10,000 runs, seed 20261014), is at least ten years of trades
(12 trades a year for these monthly cycles: 120)."""
import json, random, statistics
TARGET, RUNS, CAP = 120, 10_000, 5_000
def median_run(x, mu, sd, h, rng):
    runs = []
    for _ in range(RUNS):
        S, t = 0.0, 0
        while t < CAP:
            t += 1
            S = max(0.0, S + (mu - rng.choice(x)) / sd - 0.5)
            if S > h: break
        runs.append(t)
    return sorted(runs)[RUNS // 2]
for period in ("discovery", "challenge"):
    d = json.load(open(f"research/2026-10-12-experiment-1/results_{period}.json"))
    for code in ("SF", "SC", "BF"):
        x = [o["structures"][code]["net"] for o in d["opportunities"] if o["structures"][code]["status"] == "traded"]
        mu, sd = statistics.mean(x), statistics.stdev(x)
        h = 1.0
        while True:
            m = median_run(x, mu, sd, h, random.Random(20261014))
            if m >= TARGET or h >= 12: break
            h += 0.5
        print(f"{period} {code}: n={len(x)} h={h} (in-control median run {m} trades)")

print("-- detection at the calibrated h: 1 SD worse per trade, median run --")
def median_shift(x, mu, sd, h, shift, rng):
    runs = []
    for _ in range(4000):
        S, t = 0.0, 0
        while t < CAP:
            t += 1
            S = max(0.0, S + (mu - (rng.choice(x) + shift)) / sd - 0.5)
            if S > h: break
        runs.append(t)
    return sorted(runs)[2000]
for period, code, h in (("discovery","SF",4.5),("discovery","SC",4.5),("discovery","BF",4.0),("challenge","SF",5.5),("challenge","SC",4.0),("challenge","BF",1.0)):
    d = json.load(open(f"research/2026-10-12-experiment-1/results_{period}.json"))
    x = [o["structures"][code]["net"] for o in d["opportunities"] if o["structures"][code]["status"] == "traded"]
    mu, sd = statistics.mean(x), statistics.stdev(x)
    print(f"{period} {code} h={h}: 1 SD worse -> median {median_shift(x, mu, sd, h, -sd, random.Random(1))} trades; 0.5 SD worse -> {median_shift(x, mu, sd, h, -0.5*sd, random.Random(2))}")
