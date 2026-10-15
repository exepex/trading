"""Protocol v4 revision 7: item E's option 2 measured (judge 98 addendum 6). A crash cut, frozen before any v4 score and
defined only on outcome-side data of the scored window, makes a crash-dominated window not judgeable (no claim, no
"no") for every member. Two candidate cuts are measured:

- `vix_above_25`: the mean closing India VIX of the window's first outcome sessions is above 25 (2019-26 mean: 17.1);
- `big_share_above_10pct`: more than 10% of the window's first outcome sessions are 2% days (2017-26 base rate 4.15%).

Cost: the share of the real rolling 2019-26 windows each cut removes, per n. Re-measurement: the same paired draws as
`v4_regime_stress.py` (same seeds, thresholds unchanged), rates among the kept series, for the full period and the
busy stretches. Calm stretches are untouched by either cut, so their rows in `v4_regime_stress.md` stand.

    python tools/v4_crash_cut.py   # writes research/forecasts/v4_crash_cut.{json,md}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4_regime_stress as stress  # noqa: E402

CUTS = {
    "vix_above_25": lambda vix, big: vix > 25,
    "big_share_above_10pct": lambda vix, big: big > 0.10,
}
STRETCHES = ("full", "busy 125", "busy 250")
OUT = stress.FORECASTS / "v4_crash_cut"


def window_means(series: dict, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Mean VIX and 2%-day share of every real rolling n-session window."""
    ones = np.ones(n) / n
    return np.convolve(series["vix"], ones, "valid"), np.convolve(series["big"], ones, "valid")


def cost(question: str) -> list[dict]:
    series, rows = stress.member_series(question), []
    for n in stress.SIZES:
        vix, big = window_means(series, n)
        gate = big * n >= stress.MIN_EVENT_DAYS if stress.QUESTIONS[question][0] == "brier" else np.ones(len(vix), bool)
        for name, cut in CUTS.items():
            out = cut(vix, big)
            rows.append({"question": question, "n": n, "cut": name, "removed": float(out.mean()),
                         "judgeable_before": float(gate.mean()), "judgeable_after": float((gate & ~out).mean()),
                         "removed_days": [str(series["day"][i]) for i in np.where(out)[0][[0, -1]]] if out.any()
                         else []})  # fmt: skip
    return rows


def remeasure(question: str) -> list[dict]:
    series, rows = stress.member_series(question), []
    for name, stretch in stress.stretches(series["big"]).items():
        if name not in STRETCHES:
            continue
        for n in stress.SIZES:
            for futility in (False, True):
                for flip in (False, True):
                    d, index = stress.draw(question, series, name, stretch, n, flip, futility)
                    vix, big = series["vix"][index].mean(axis=1), series["big"][index].mean(axis=1)
                    local = stress.local_improvement(d, series["b"], stretch)
                    estimate = -d[index].mean(axis=1) / series["b"][index].mean(axis=1)
                    for cut_name, cut in CUTS.items():
                        keep = ~cut(vix, big)
                        rate, _ = stress.verdict_rates(question, n, d, series, index, futility, keep)
                        rows.append({"question": question, "n": n, "stretch": name, "cut": cut_name,
                                     "kind": "futility" if futility else "claim", "kept": float(keep.mean()),
                                     "orientation": "flipped" if flip else "as measured", "rate": rate,
                                     "local_improvement": local,
                                     "kept_median_estimate": float(np.median(estimate[keep])) if keep.any()
                                     else None})  # fmt: skip
                    print(rows[-1], flush=True)
    return rows


def markdown(costs: list[dict], rows: list[dict]) -> str:
    lines = [
        "# Protocol v4: item E option 2, crash cuts measured (`tools/v4_crash_cut.py`)",
        "",
        "## Cost: real rolling 2019-26 windows removed",
        "",
        "| question | n | cut | removed | judgeable before | judgeable after | removed windows start |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in costs:
        span = " to ".join(c["removed_days"])
        lines.append(f"| {c['question']} | {c['n']} | {c['cut']} | {100 * c['removed']:.1f}% | "
                     f"{100 * c['judgeable_before']:.0f}% | {100 * c['judgeable_after']:.0f}% | {span} |")  # fmt: skip
    lines += [
        "",
        "## Re-measured: rates among kept series (paired with `v4_regime_stress.md`)",
        "",
        "Marks as in `v4_regime_stress.md`: **bold** false verdict above nominal + 2 Monte Carlo SE of the kept count,"
        " *italic* above it but the regime's truth (local = the whole stretch's true improvement). The kept median"
        ' estimate is the median measured improvement of the kept series: below the minimum effect, a "no" there'
        " agrees with what the kept (calmer) windows show. A stretch with almost nothing kept says little.",
        "",
        "| question | stretch | n | orientation | cut | kept | claim | futility | local (futility null) | "
        "kept median estimate (futility null) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    keyed = {(r["question"], r["stretch"], r["n"], r["orientation"], r["cut"], r["kind"]): r for r in rows}
    for (q, s, n, o, cut, kind), r in keyed.items():
        if kind != "claim":
            continue
        f, kept = keyed[(q, s, n, o, cut, "futility")], max(1, round(r["kept"] * stress.SERIES))
        margin = stress.QUESTIONS[q][3]
        claim = _mark(r["rate"], r["local_improvement"] > 0, stress.CLAIM_NOMINAL, kept)
        futility = _mark(f["rate"], f["local_improvement"] < margin, 0.025, kept)
        lines.append(f"| {q} | {s} | {n} | {o} | {cut} | {100 * r['kept']:.1f}% | {claim} | {futility} | "
                     f"{f['local_improvement']:+.3f} | {_estimate(f['kept_median_estimate'])} |")  # fmt: skip
    return "\n".join(lines) + "\n"


def _estimate(value: float | None) -> str:
    return "none kept" if value is None else f"{value:+.3f}"


def _mark(rate: float, regime_truth: bool, nominal: float, count: int) -> str:
    text = f"{100 * rate:.2f}%"
    if rate <= stress.study.tolerance(nominal, count):
        return text
    return f"*{text}*" if regime_truth else f"**{text}**"


def main() -> None:
    costs = [c for q in stress.QUESTIONS for c in cost(q)]
    rows = [r for q in stress.QUESTIONS for r in remeasure(q)]
    OUT.with_suffix(".json").write_text(json.dumps({"cost": costs, "rows": rows}, indent=1) + "\n", encoding="utf-8")
    OUT.with_suffix(".md").write_text(markdown(costs, rows), encoding="utf-8")


if __name__ == "__main__":
    main()
