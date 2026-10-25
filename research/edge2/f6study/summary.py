"""F6's statistics and nomination (protocol section 6): mean net with a Newey-West standard error (lag 0 for H1, 4 for
H5's overlapping trades), the one-sided p, Holm across the six, the always-long and random-sign controls, and the
report's figures. Rows are `trades.trade` dicts."""

from __future__ import annotations

import math
import random
from collections.abc import Mapping, Sequence

from fno.scoreboard.uncertainty import holm

ALPHA, RS_DRAWS, RS_SEED, GATE_P_MAX, NOMINATED_AT_MOST = 0.05, 2000, 20261025, 0.10, 2
NW_LAG = {"H1": 0, "H5": 4}
HALVES = (("2019", "2021"), ("2022", "2024"))


def taken(rows: Sequence[dict]) -> list[dict]:
    return [r for r in rows if r["status"] == "taken"]


def mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def newey_west_se(values: Sequence[float], lag: int) -> float | None:
    n = len(values)
    if n < 2:
        return None
    m = sum(values) / n
    d = [v - m for v in values]
    variance = sum(x * x for x in d) / n
    for k in range(1, lag + 1):
        variance += 2 * (1 - k / (lag + 1)) * sum(d[i] * d[i - k] for i in range(k, n)) / n
    return math.sqrt(max(variance, 0.0) / n)


def one_sided_p(m: float | None, se: float | None) -> float:
    return 1.0 if m is None or not se else 0.5 * math.erfc(m / se / math.sqrt(2))


def random_sign_p(rows: Sequence[dict], observed: float | None) -> float | None:
    """Share of random sign series (the same days, the same number of longs) whose mean net is >= the observed."""
    if observed is None or not rows:
        return None
    longs = sum(r["side"] > 0 for r in rows)
    rng, hits = random.Random(RS_SEED), 0
    for _ in range(RS_DRAWS):
        signs = [1] * longs + [-1] * (len(rows) - longs)
        rng.shuffle(signs)
        nets = [s * r["side"] * r["gross"] - r["charges"] - r["pads"] for s, r in zip(signs, rows, strict=True)]
        hits += sum(nets) / len(nets) >= observed
    return hits / RS_DRAWS


def always_long(rows: Sequence[dict]) -> float | None:
    """The same days held long: gross with the sign of a long, the same charges and pads (charges differ by side only
    in which leg pays STT and stamp; that difference is ignored here, as a control only)."""
    return mean([r["side"] * r["gross"] - r["charges"] - r["pads"] for r in rows])


def drawdown(rows: Sequence[dict], step: int) -> float:
    peak, low, total = 0.0, 0.0, 0.0
    for r in rows[::step]:
        total += r["net"]
        peak = max(peak, total)
        low = min(low, total - peak)
    return low


def describe(rows: Sequence[dict], pad2: Sequence[dict], hist: Sequence[dict], horizon: str) -> dict:
    done = taken(rows)
    nets = [r["net"] for r in done]
    m, se = mean(nets), newey_west_se(nets, NW_LAG[horizon])
    halves = {f"{a}-{b}": mean([r["net"] for r in done if a <= r["exit"][:4] <= b]) for a, b in HALVES}
    sd = math.sqrt(sum((x - m) ** 2 for x in nets) / (len(nets) - 1)) if len(nets) > 1 else None
    years = sorted({r["exit"][:4] for r in done})
    return {
        "signals": len(rows), "taken": len(done),
        "skips": {k: sum(r["status"] == k for r in rows) for k in sorted({r["status"] for r in rows}) if k != "taken"},
        "mean_gross": mean([r["gross"] for r in done]), "mean_charges": mean([r["charges"] for r in done]),
        "mean_pads": mean([r["pads"] for r in done]), "mean_net": m, "se": se, "p": one_sided_p(m, se),
        "mean_net_pad2": mean([r["net"] for r in taken(pad2)]),
        "mean_net_hist_stt": mean([r["net"] for r in taken(hist)]),
        "win_share": sum(x > 0 for x in nets) / len(nets) if nets else None, "worst_trade": min(nets, default=None),
        "max_drawdown": drawdown(done, 1 if horizon == "H1" else 5), "halves": halves,
        "long_mean": mean([r["net"] for r in done if r["side"] > 0]),
        "short_mean": mean([r["net"] for r in done if r["side"] < 0]),
        "long_share": sum(r["side"] > 0 for r in done) / len(done) if done else None,
        "by_year": {y: mean([r["net"] for r in done if r["exit"][:4] == y]) for y in years},
        "always_long": always_long(done), "p_sign": random_sign_p(done, m), "sd": sd,
        "sample_plan": None if not m or m <= 0 or sd is None else math.ceil((1.645 * sd / m) ** 2),
    }  # fmt: skip


def family(runs: Mapping[str, Mapping[str, list[dict]]]) -> dict[str, dict]:
    """`runs[name]` = {"pad1", "pad2", "hist"} rows; name is EDGE2-F6-<signal>-<horizon>."""
    rows = {name: describe(r["pad1"], r["pad2"], r["hist"], name.rsplit("-", 1)[1]) for name, r in runs.items()}
    names = sorted(rows)
    for name, passed in zip(names, holm([rows[n]["p"] for n in names], ALPHA), strict=True):
        rows[name]["holm"] = passed
    return rows


def eligible(r: dict) -> bool:
    halves = all(v is not None and v > 0 for v in r["halves"].values())
    pad2 = r["mean_net_pad2"] is not None and r["mean_net_pad2"] > 0
    return r["holm"] and pad2 and r["p_sign"] is not None and r["p_sign"] <= GATE_P_MAX and halves


def nominated(rows: Mapping[str, dict]) -> list[str]:
    return sorted((n for n, r in rows.items() if eligible(r)), key=lambda n: (rows[n]["p"], n))[:NOMINATED_AT_MOST]
