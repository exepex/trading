"""Response 198 (exploratory, one window, no freeze): runs the three candidates as pre-declared in its part 1.

    python -I research/breadth/candidates/prep.py <scratch>/panel.csv <scratch>/daily.json
    python -I research/breadth/candidates/run.py <scratch>/daily.json research/breadth/candidates/results.json

Paths are study 3's (`block_paths`: its seed words, 63-session blocks, the same starts for every member); population
numbers 0 (whole window) and 1 (2024, the worst year) are study 3's, 2 (2025, C's hold-out) is new."""

import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "studies"), str(HERE.parents[2])]

import compare as c  # noqa: E402
from brstudy import study3  # noqa: E402
from brstudy.stats import look_counts  # noqa: E402

DELTA = 0.0038481856299512163  # study 1
WORST_VARIANCE = 0.0006660642807131222  # study 2: 2024, market/trail60
POWER_PATHS = 1000
SIGNS = {"+d": 1, "-d": -1}
START = time.time()


def log(*what) -> None:
    print(f"[{time.time() - START:7.0f}s]", *what, flush=True)


class Data:
    def __init__(self, document: dict):
        self.days = document["days"]
        self.members = np.array(list(document["members"].values()))
        self.big = np.array(document["nifty_big"], dtype=bool)
        self.populations = {"whole": (0, np.arange(len(self.days))),
                            "worst_year": (1, self._year("2024")), "holdout_2025": (2, self._year("2025"))}  # fmt: skip

    def _year(self, year: str) -> np.ndarray:
        return np.array([i for i, d in enumerate(self.days) if d.startswith(year)])

    def paths(self, population: str, length: int, centre, paths: int = study3.PATHS) -> tuple:
        number, days = self.populations[population]
        index = study3.block_paths(len(days), paths, length, number)
        return centre(self.members[:, days])[:, index], self.big[days][index]


def null_rates(data, pool, population, looks, alpha, transform, centre, gate) -> dict:
    """False-claim rates per sign on one population's null paths."""
    member_paths, big_paths = data.paths(population, looks[1], centre)
    out = {}
    for name, sign in SIGNS.items():
        series = transform(sign * member_paths)
        claims = [c.path_claims(series, look, alpha, pool) for look in looks]
        if gate:
            claims = [hit & c.judgeable(big_paths, look) for hit, look in zip(claims, looks, strict=True)]
        out[name] = c.rates(*claims)
        log(population, name, f"alpha {alpha}", out[name]["either"])
        if gate:
            out[name]["judgeable"] = [float(c.judgeable(big_paths, look).mean()) for look in looks]
    return out


def power(data, pool, looks, alpha, transform, gate) -> dict:
    """+d, whole window: one member at a time improved by exactly delta, the others null; Holm claims that member."""
    member_paths, big_paths = data.paths("whole", looks[1], study3.centred, POWER_PATHS)
    per_member = []
    for member in range(c.K):
        shifted = member_paths.copy()
        shifted[member] -= DELTA
        series = transform(shifted)
        claims = [c.member_claimed(c.p_values(series, look, alpha, pool), member, alpha) for look in looks]
        if gate:
            claims = [hit & c.judgeable(big_paths, look) for hit, look in zip(claims, looks, strict=True)]
        per_member.append(c.rates(*claims))
        log("power member", member, f"alpha {alpha}", per_member[-1]["either"])
    return {key: float(np.mean([r[key] for r in per_member])) for key in per_member[0]} | {"per_member": per_member}


def single_loop(data, pool, transform, centre, gate, meaning_check=False) -> dict:
    tried = []
    for rate in study3.RATES:
        looks = look_counts(rate, WORST_VARIANCE, DELTA)
        result = {"rate": rate, "looks": list(looks), "false_claim": {}}
        for population in ("whole", "worst_year"):
            result["false_claim"][population] = null_rates(data, pool, population, looks, rate, transform, centre, gate)
            if meaning_check:
                result["false_claim"][f"{population}/mean_centred"] = null_rates(
                    data, pool, population, looks, rate, transform, study3.centred, gate)  # fmt: skip
        tried.append(result)
        if passes(result["false_claim"]):
            break
    selected = tried[-1] if passes(tried[-1]["false_claim"]) else None
    at = selected or tried[0]
    return {"loop": tried, "selected_rate": selected and selected["rate"],
            "power": power(data, pool, tuple(at["looks"]), at["rate"], transform, gate),
            "power_at_rate": at["rate"]}  # fmt: skip


def passes(false_claim: dict) -> bool:
    return all(c.within(r) for population in false_claim.values() for r in population.values())


def calibrated(data, pool) -> dict:
    looks = look_counts(0.02, WORST_VARIANCE, DELTA)
    ps = {}
    for population in ("worst_year", "holdout_2025", "whole"):
        member_paths, _ = data.paths(population, looks[1], study3.centred)
        for name, sign in SIGNS.items():
            ps[(population, name)] = [c.p_values(sign * member_paths, look, 0.02 / c.K, pool) for look in looks]
    alpha = c.calibrated_alpha({k: v for k, v in ps.items() if k[0] == "worst_year"}, looks)
    report = alpha if alpha is not None else float(c.GRID[0])
    checked = {f"{p}/{s}": c.rates(c.any_claim(p1, report), c.any_claim(p2, report)) for (p, s), (p1, p2) in ps.items()}
    return {"looks": list(looks), "alpha_star": alpha, "false_claim": checked, "passes": alpha is not None and
            all(c.within(r) for r in checked.values()),
            "power": power(data, pool, looks, report, lambda x: x, False)}  # fmt: skip


def main(daily_json: str, out: str) -> None:
    data = Data(json.loads(Path(daily_json).read_text()))
    result = {}
    with Pool(4) as pool:
        for name, run in (("A_v4_crash_gate", lambda: single_loop(data, pool, lambda x: x, study3.centred, gate=True)),
                          ("B_daily_sign", lambda: single_loop(data, pool, np.sign, c.median_centred, gate=False,
                                                               meaning_check=True)),
                          ("C_calibrated", lambda: calibrated(data, pool))):  # fmt: skip
            log("start", name)
            result[name] = run()
            Path(out).write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:])
