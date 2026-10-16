"""ChatGPT review 134, point 1: LR3's threshold with a chronological circular-block resampling (blocks of 3
consecutive trades) beside the iid one, on experiment 1's nets in decision-day order. The frozen h is the larger of the
two, rounded up to 0.5, with a floor of 4; the target is an in-control median run of ten years of trades (120)."""
import json, random, statistics
TARGET, RUNS, CAP, BLOCK = 120, 10_000, 5_000, 3

def draw_iid(x, rng):
    while True:
        yield rng.choice(x)

def draw_blocks(x, rng):
    n = len(x)
    while True:
        start = rng.randrange(n)
        for i in range(BLOCK):
            yield x[(start + i) % n]

def median_run(x, mu, sd, h, draw, seed):
    rng, runs = random.Random(seed), []
    for _ in range(RUNS):
        S, t, stream = 0.0, 0, draw(x, rng)
        while t < CAP:
            t += 1
            S = max(0.0, S + (mu - next(stream)) / sd - 0.5)
            if S > h:
                break
        runs.append(t)
    return sorted(runs)[RUNS // 2]

def calibrate(x, draw):
    mu, sd, h = statistics.mean(x), statistics.stdev(x), 1.0
    while h < 12 and median_run(x, mu, sd, h, draw, 20261014) < TARGET:
        h += 0.5
    return h

for period in ("discovery", "challenge"):
    d = json.load(open(f"research/2026-10-12-experiment-1/results_{period}.json"))
    for code in ("SF", "SC", "BF"):
        rows = sorted((o for o in d["opportunities"] if o["structures"][code]["status"] == "traded"),
                      key=lambda o: o["cycle"]["decision_day"])
        x = [o["structures"][code]["net"] for o in rows]
        iid, blocks = calibrate(x, draw_iid), calibrate(x, draw_blocks)
        span = f"{rows[0]['cycle']['decision_day']}..{rows[-1]['cycle']['decision_day']}"
        print(f"{period} {code}: n={len(x)} span {span} iid h*={iid} block h*={blocks} frozen h={max(4.0, iid, blocks)}")
