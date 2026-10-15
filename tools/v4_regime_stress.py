"""Protocol v4 revision 7: every judgeable member's claim and futility rules inside one regime (judge 98 addendum 6).

Revision 6 stressed V6b alone; the judge showed its crash-window "failures" are regime-local truth (inside the 2020
crash the full-period null's local mean is far from zero), and asked the same check for V1, V2 and V6a, since futility
drives the stop rule's Test A "no". For each member (V1 and V2 QLIKE, V6a and V6b Brier) the full-period null of
2019-26 (exposed regular sessions from the first day with a valid V6 base rate) is resampled in circular 20-session
blocks over the full period and **inside** the busiest and the calmest 125 and 250 sessions by 2% days, both
orientations, at n = 125 and 250. The operative thresholds are applied unchanged (QLIKE: `v4_claim_thresholds.json`
and `v4_futility_study.json`; Brier: the banded thresholds of `v4_brier_bands.json`, judged only with 5 or more 2%
days). Each row prints the **local true relative improvement** inside the stretch: below the minimum effect, a "no" is
the truth of that regime; above it, a "no" is a false "no".

    python tools/v4_regime_stress.py   # writes research/forecasts/v4_regime_stress.{json,md}
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import v4_brier_bands as bands  # noqa: E402
import v4_brier_regimes as regimes  # noqa: E402
import v4_size_study as study  # noqa: E402

from fno.constants import V1_RV_1S, V2_RV_5S, V6_BIG_MOVE_1S, V6_BIG_MOVE_5S  # noqa: E402
from fno.forecast_v4.confirmatory import MIN_EVENT_DAYS  # noqa: E402
from fno.forecast_v4.student_t import t_cdf  # noqa: E402

SEED, SERIES, SIZES = 20261015, 100_000, (125, 250)
CLAIM_NOMINAL = 0.02 / 15  # look 1, Holm's first step
QUESTIONS = {V1_RV_1S: ("qlike", 1, 5, 0.03), V2_RV_5S: ("qlike", 5, 10, 0.03),
             V6_BIG_MOVE_1S: ("brier", 1, 5, 0.02), V6_BIG_MOVE_5S: ("brier", 5, 10, 0.02)}  # fmt: skip
FORECASTS = ROOT / "research" / "forecasts"
OUT = FORECASTS / "v4_regime_stress"


def _rows() -> list[dict]:
    with open(ROOT / "research/data/nifty-panel/warmup_closes.csv", encoding="utf-8") as handle:
        return [r for r in csv.DictReader(handle) if r["session"] == "regular" and r["date"] <= "2026-10-14"]


def qlike_series(horizon: int, since: str) -> dict[str, np.ndarray]:
    """V1/V2's trailing-5 minus trailing-20 ranking-loss difference, the baseline's textbook QLIKE, the 2% flag and
    the closing VIX of each forecast's first outcome session, on RV > 0 dates from `since` (exposed data)."""
    rows = _rows()
    returns = np.diff(np.log([float(r["underlying"]) for r in rows]))
    r2, out = returns**2, {"d": [], "b": [], "big": [], "vix": [], "day": []}
    for t in range(20, len(r2) - horizon + 1):
        rv, f5, f20 = r2[t : t + horizon].sum(), r2[t - 5 : t].mean() * horizon, r2[t - 20 : t].mean() * horizon
        if rows[t + 1]["date"] < since or not (f5 > 0 and f20 > 0 and rv > 0):
            continue
        out["d"].append(math.log(f5) + rv / f5 - math.log(f20) - rv / f20)
        out["b"].append(rv / f20 - math.log(rv / f20) - 1)
        out["big"].append(float(abs(returns[t]) >= 0.02))
        out["vix"].append(float(rows[t + 1]["vix"]))
        out["day"].append(rows[t + 1]["date"])
    return {k: np.asarray(v) for k, v in out.items()}


def brier_series(horizon: int) -> dict[str, np.ndarray]:
    series = regimes.brier_series(horizon)
    vix = {r["date"]: float(r["vix"]) for r in _rows()}
    return series | {"vix": np.array([vix[day] for day in series["day"]])}


def member_series(question: str) -> dict[str, np.ndarray]:
    kind, horizon, _, _ = QUESTIONS[question]
    if kind == "brier":
        return brier_series(horizon)
    return qlike_series(horizon, str(brier_series(1)["day"][0]))  # one exposed span for every member


def stretches(big: np.ndarray) -> dict[str, tuple[int, int] | None]:
    out: dict[str, tuple[int, int] | None] = {"full": None}
    for length in (125, 250):
        counts = np.convolve(big, np.ones(length), "valid")
        out[f"busy {length}"] = (int(np.argmax(counts)), int(np.argmax(counts)) + length)
        out[f"calm {length}"] = (int(np.argmin(counts)), int(np.argmin(counts)) + length)
    return out


def null(series: dict, flip: bool, futility: bool, margin: float) -> np.ndarray:
    """Centred over the full period (claims) or shifted to a true improvement of exactly the margin (futility)."""
    centred = series["d"] - series["d"].mean()
    centred = -centred if flip else centred
    return centred - margin * series["b"].mean() if futility else centred


def local_improvement(d: np.ndarray, b: np.ndarray, stretch: tuple[int, int] | None) -> float:
    lo, hi = stretch if stretch else (0, len(d))
    return float(-d[lo:hi].mean() / b[lo:hi].mean())


def resample_index(length: int, n: int, count: int, rng: np.random.Generator, stretch) -> np.ndarray:
    lo, hi = stretch if stretch else (0, length)
    starts = rng.integers(0, hi - lo, size=(count, math.ceil(n / study.REAL_BLOCK)))
    return (lo + (starts[:, :, None] + np.arange(study.REAL_BLOCK)) % (hi - lo)).reshape(count, -1)[:, :n]


def batch_t(x: np.ndarray, block: int) -> tuple[np.ndarray, int]:
    t, _, k = study.batch_stats(x, block)
    return np.where(np.isfinite(t), t, np.inf), k


def t_at(p: float, df: int) -> float:
    """The t at which the batch-means p equals p (bisection on `t_cdf`): p <= tau exactly when t <= t_at(tau)."""
    if p <= 0:
        return -np.inf
    lo, hi = -1e6, 0.0 if p < 0.5 else 1e6
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if t_cdf(mid, df) < p else (lo, mid)
    return lo


def thresholds(question: str, n: int) -> dict:
    """{band or None: (claim look-1 threshold, futility threshold)} as G8 would use them at this n."""
    if QUESTIONS[question][0] == "qlike":
        claim = json.loads((FORECASTS / "v4_claim_thresholds.json").read_text(encoding="utf-8"))["rows"]
        futility = json.loads((FORECASTS / "v4_futility_study.json").read_text(encoding="utf-8"))["cells"]
        c = next(r["threshold"] for r in claim if (r["question"], r["n"], r["look"]) == (question, n, "look 1"))
        f = next(r["threshold"] for r in futility if (r["question"], r["n"]) == (question, n))
        return {None: (c, f)}
    rows = json.loads((FORECASTS / "v4_brier_bands.json").read_text(encoding="utf-8"))["rows"]
    return {tuple(r["band"]): (r["look 1"]["claim_threshold"], r["futility_threshold"]) for r in rows
            if (r["question"], r["n"]) == (question, n)}  # fmt: skip


def verdict_rates(
    question: str,
    n: int,
    d: np.ndarray,
    series: dict,
    index: np.ndarray,
    futility: bool,
    keep: np.ndarray | None = None,
) -> tuple[float, float]:
    """(rate of the verdict among the kept series, share of all series judged). A claim also needs the point estimate
    at or above the minimum effect (`family`); `keep` is option 2's crash cut (None: every series kept)."""
    kind, _, block, margin = QUESTIONS[question]
    xd, xb, events = d[index], series["b"][index], series["big"][index].sum(axis=1)
    t, k = batch_t(-(xd + margin * xb) if futility else xd, block)
    keep = np.ones(len(index), bool) if keep is None else keep
    judged = keep & (events >= MIN_EVENT_DAYS if kind == "brier" else True)
    if not futility:
        judged &= -xd.mean(axis=1) / xb.mean(axis=1) >= margin
    found = np.zeros(len(index), bool)
    for band, (claim, fut) in thresholds(question, n).items():
        chosen = judged if band is None else judged & bands.in_band(events, band)
        found |= chosen & (t <= t_at(fut if futility else claim, k - 1))
    return float(found.sum() / max(keep.sum(), 1)), float((keep & (events >= MIN_EVENT_DAYS if kind == "brier"
                                                                     else True)).mean())  # fmt: skip


def draw(question: str, series: dict, name: str, stretch, n: int, flip: bool, futility: bool):
    """The null difference and the resample index of one cell (seeded by the cell)."""
    _, _, block, margin = QUESTIONS[question]
    word = [SEED, 707, block, n, len(name), int(name.startswith("busy")), int(flip), int(futility)]
    d = null(series, flip, futility, margin)
    return d, resample_index(len(d), n, SERIES, np.random.default_rng(np.random.SeedSequence(word)), stretch)


def run_question(question: str) -> list[dict]:
    margin = QUESTIONS[question][3]
    series, rows = member_series(question), []
    for name, stretch in stretches(series["big"]).items():
        lo, hi = stretch if stretch else (0, len(series["d"]))
        for n in SIZES:
            for futility in (False, True):
                for flip in (False, True):
                    d, index = draw(question, series, name, stretch, n, flip, futility)
                    rate, judged = verdict_rates(question, n, d, series, index, futility)
                    rows.append({"question": question, "n": n, "stretch": name, "days": [series["day"][lo],
                                 series["day"][hi - 1]], "big_days": int(series["big"][lo:hi].sum()),
                                 "mean_vix": float(series["vix"][lo:hi].mean()), "kind": "futility" if futility
                                 else "claim", "orientation": "flipped" if flip else "as measured", "rate": rate,
                                 "judged": judged, "local_improvement": local_improvement(d, series["b"], stretch),
                                 "margin": margin})  # fmt: skip
                    print(rows[-1], flush=True)
    return rows


def markdown(rows: list[dict]) -> str:
    lines = [
        "# Protocol v4: every member's rules inside one regime (`tools/v4_regime_stress.py`)",
        "",
        f"{SERIES:,} series per cell; operative thresholds unchanged. Claims: look 1, null centred over 2019-26 "
        "(nominal 0.133%; a claim also needs the point estimate at the minimum effect). Futility: null shifted to a "
        "full-period true improvement of exactly the minimum effect (target 2.5%). **local** = the true relative "
        'improvement inside the stretch: a futility "no" is false only where local >= the minimum effect, a claim '
        "only where local <= 0. **Bold**: a false verdict above nominal + 2 Monte Carlo SE; *italic*: above it, but "
        "the regime's truth. Exposed data; Brier members judged only with 5+ 2% days.",
        "",
        "| question | stretch | n | orientation | claim | local (claim null) | futility | local (futility null) | "
        "judged |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    keyed = {(r["question"], r["stretch"], r["n"], r["orientation"], r["kind"]): r for r in rows}
    for (q, s, n, o, kind), r in keyed.items():
        if kind != "claim":
            continue
        f = keyed[(q, s, n, o, "futility")]
        lines.append(
            f"| {q} | {s} ({r['days'][0]} to {r['days'][1]}; {r['big_days']} 2% days, VIX {r['mean_vix']:.1f}) | "
            f"{n} | {o} | {_pct(r['rate'], r['local_improvement'] > 0, CLAIM_NOMINAL)} | "
            f"{r['local_improvement']:+.3f} | "
            f"{_pct(f['rate'], f['local_improvement'] < f['margin'], 0.025)} | {f['local_improvement']:+.3f} | "
            f"{100 * f['judged']:.0f}% |"
        )
    return "\n".join(lines) + "\n"


def _pct(rate: float, regime_truth: bool, nominal: float) -> str:
    """Bold above nominal + 2 Monte Carlo SE only where the verdict is false for that regime; italic where it is the
    regime's truth."""
    text = f"{100 * rate:.2f}%"
    if rate <= study.tolerance(nominal, SERIES):
        return text
    return f"*{text}*" if regime_truth else f"**{text}**"


def main() -> None:
    rows = [r for q in QUESTIONS for r in run_question(q)]
    OUT.with_suffix(".json").write_text(json.dumps({"series": SERIES, "rows": rows}, indent=1) + "\n", encoding="utf-8")
    OUT.with_suffix(".md").write_text(markdown(rows), encoding="utf-8")


if __name__ == "__main__":
    main()
