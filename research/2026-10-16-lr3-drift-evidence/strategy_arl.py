"""Design 5.8's strategy CUSUM on experiment 1's real per-trade nets (challenge 2019-2023 and discovery): the lower
CUSUM S = max(0, S + (mu0 - x)/sigma - k), alarm at S > h, with mu0 and sigma the sample's own mean and SD (the
"registered" values when in control). Run length by resampling the trades with replacement, 4,000 runs."""
import json, random, statistics
rng = random.Random(20261016)
for period in ("discovery", "challenge"):
    d = json.load(open(f"research/2026-10-12-experiment-1/results_{period}.json"))
    for code in ("SF", "SC", "BF"):
        x = [o["structures"][code]["net"] for o in d["opportunities"] if o["structures"][code]["status"] == "traded"]
        mu, sd = statistics.mean(x), statistics.stdev(x)
        skew = sum((v - mu) ** 3 for v in x) / len(x) / sd ** 3
        res = []
        for label, shift in (("in control", 0.0), ("edge gone", -mu), ("1 SD worse", -sd)):
            for h in (4,):
                runs = []
                for _ in range(4000):
                    S, t = 0.0, 0
                    while t < 3000:
                        t += 1
                        S = max(0.0, S + (mu - (rng.choice(x) + shift)) / sd - 0.5)
                        if S > h: break
                    runs.append(t)
                runs.sort()
                res.append(f"{label}: median {runs[2000]}, 10th pct {runs[400]}")
        print(f"{period} {code}: n={len(x)} mean Rs {mu:,.0f} sd Rs {sd:,.0f} (edge {mu/sd:+.2f} SD) skew {skew:+.2f} min Rs {min(x):,.0f} | " + " | ".join(res))
