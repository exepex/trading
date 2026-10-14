"""The frozen study's statistics and report (PROTOCOL.md sections 4 and 6): Part 1 per structure, Part 2 per colour,
and the 2020 and 2024 crash windows. Writes results.json and results.md."""

from __future__ import annotations

import json
import math
import random
import statistics as st
from datetime import date
from pathlib import Path

from study import CRASH_2020, CRASH_2024, HIT, RESAMPLES, SEED, STRUCTURES, T_PASS, WELCH_PASS

NAMES = {"W1": "bought call", "W2": "bought put", "W3": "bull call spread", "W4": "bear put spread",
         "W5": "short iron condor"}  # fmt: skip
COLOURS = ("GREEN", "AMBER", "RED")


def taken(rows: list[dict], code: str) -> list[dict]:
    return [r | r["trades"][code] for r in rows if r["trades"][code]["status"] == "traded"]


def hit(t: dict) -> bool:
    return t["net"] <= -HIT * t["max_loss"]


def bootstrap_low(nets: list[float]) -> float:
    rng = random.Random(SEED)
    means = sorted(st.mean(rng.choices(nets, k=len(nets))) for _ in range(RESAMPLES))
    return means[RESAMPLES // 100]


def summary(trades: list[dict]) -> dict:
    nets = [t["net"] for t in trades]
    if len(nets) < 2:
        return {"n": len(nets), "total": sum(nets)}
    mean, sd = st.mean(nets), st.stdev(nets)
    return {"n": len(nets), "total": sum(nets), "mean": mean, "sd": sd, "t": mean / (sd / math.sqrt(len(nets))),
            "win_rate": sum(n > 0 for n in nets) / len(nets), "worst": min(nets),
            "mean_gross": st.mean(t["gross"] for t in trades), "mean_costs": st.mean(t["costs"] for t in trades),
            "max_loss_hits": sum(hit(t) for t in trades),
            "trades_for_2se": (2 * sd / mean) ** 2 if mean > 0 else None}  # fmt: skip


def part1(rows: list[dict], code: str) -> dict:
    trades = taken(rows, code)
    early = [t for t in trades if t["entry"] < "2024"]
    late = [t for t in trades if t["entry"] >= "2024"]
    whole, years = summary(trades), (date.fromisoformat(rows[-1]["expiry"]) - date(2019, 1, 1)).days / 365.25
    statuses = [r["trades"][code]["status"] for r in rows]
    whole |= {"per_year": len(trades) / years, "boot_low_1pct": bootstrap_low([t["net"] for t in trades]),
              "statuses": {s: statuses.count(s) for s in sorted(set(statuses))},
              "2019_2023": summary(early), "2024_2026": summary(late)}  # fmt: skip
    whole["pass"] = bool(
        whole["2019_2023"].get("mean", -1) > 0 and whole["2024_2026"].get("mean", -1) > 0
        and whole["t"] >= T_PASS and whole["boot_low_1pct"] > 0
    )  # fmt: skip
    return whole


def welch(a: list[float], b: list[float]) -> float:
    return (st.mean(b) - st.mean(a)) / math.sqrt(st.variance(a) / len(a) + st.variance(b) / len(b))


def part2(rows: list[dict], code: str) -> dict:
    trades = taken(rows, code)
    by = {c: [t for t in trades if t["weather"] == c] for c in COLOURS}
    red, rest = by["RED"], by["GREEN"] + by["AMBER"]
    out = {c: summary(by[c]) | {"hit_rate": sum(map(hit, by[c])) / len(by[c]) if by[c] else None} for c in COLOURS}
    out["non_red"] = summary(rest) | {"hit_rate": sum(map(hit, rest)) / len(rest) if rest else None}
    if len(red) >= 2 and len(rest) >= 2:
        t = welch([x["net"] for x in red], [x["net"] for x in rest])
        worse_hits = out["RED"]["hit_rate"] >= out["non_red"]["hit_rate"]
        out |= {"welch_t_red_worse": t, "filter_helps": bool(t >= WELCH_PASS and worse_hits)}
    out["cost_of_staying_out"] = sum(x["net"] for x in red)
    out["total_without_red"] = sum(x["net"] for x in rest)
    return out


def crashes(rows: list[dict]) -> dict:
    window_2020 = [r for r in rows if CRASH_2020[0].isoformat() <= r["entry"] <= CRASH_2020[1].isoformat()]
    day = CRASH_2024.isoformat()
    window_2024 = [r for r in rows if r["entry"] <= day <= r["expiry"]]

    def show(group):
        return [{"entry": r["entry"], "expiry": r["expiry"], "weather": r["weather"],
                 "nets": {c: round(r["trades"][c]["net"]) if r["trades"][c]["status"] == "traded"
                          else r["trades"][c]["status"] for c in STRUCTURES}} for r in group]  # fmt: skip

    return {"2020": show(window_2020), "2024": show(window_2024)}


def write_report(rows: list[dict], folder: Path) -> None:
    results = {"opportunities": len(rows), "weather_counts": {c: sum(r["weather"] == c for r in rows) for c in COLOURS},
               "part1": {c: part1(rows, c) for c in STRUCTURES}, "part2": {c: part2(rows, c) for c in STRUCTURES},
               "crashes": crashes(rows)}  # fmt: skip
    (folder / "results.json").write_text(json.dumps(results, indent=1, default=str) + "\n")
    (folder / "trades.json").write_text(json.dumps(rows, indent=0, default=str) + "\n")
    (folder / "results.md").write_text(markdown(results))
    print(markdown(results))


def money(x) -> str:
    return "-" if x is None else f"{x:,.0f}"


def markdown(res: dict) -> str:
    lines = ["# Weekly options and weather: results (frozen protocol, one run)", "",
             f"Opportunities {res['opportunities']}; weather {res['weather_counts']}", "", "## Part 1", "",
             "| Id | Structure | n | per year | mean net | SD | t | 1% boot low | 2019-23 mean | 2024-26 mean | "
             "gross | costs | worst | max-loss hits | trades for 2 SE | pass |", "|" + "---|" * 16]  # fmt: skip
    for code, p in res["part1"].items():
        lines.append(
            f"| {code} | {NAMES[code]} | {p['n']} | {p['per_year']:.1f} | {money(p.get('mean'))} | "
            f"{money(p.get('sd'))} | {p.get('t', 0):.2f} | {money(p['boot_low_1pct'])} | "
            f"{money(p['2019_2023'].get('mean'))} | "
            f"{money(p['2024_2026'].get('mean'))} | {money(p.get('mean_gross'))} | {money(p.get('mean_costs'))} | "
            f"{money(p.get('worst'))} | {p.get('max_loss_hits')} | {money(p.get('trades_for_2se'))} | {p['pass']} |"
        )
    lines += ["", "## Part 2 (RED vs non-RED)", "",
              "| Id | GREEN n / mean | AMBER n / mean | RED n / mean | hit rate RED / non-RED | Welch t | helps | "
              "cost of staying out | total without RED |", "|" + "---|" * 9]  # fmt: skip
    for code, p in res["part2"].items():
        cells = [f"{p[c]['n']} / {money(p[c].get('mean'))}" for c in COLOURS]
        rates = f"{p['RED']['hit_rate'] or 0:.0%} / {p['non_red']['hit_rate'] or 0:.0%}"
        verdict = f"{p.get('welch_t_red_worse', 0):.2f} | {p.get('filter_helps')}"
        stay_out = f"{money(p['cost_of_staying_out'])} | {money(p['total_without_red'])}"
        lines.append(f"| {code} | {' | '.join(cells)} | {rates} | {verdict} | {stay_out} |")
    for year, group in res["crashes"].items():
        lines += ["", f"## Crash window {year}", ""]
        lines += [f"- {g['entry']} to {g['expiry']}: {g['weather']}, nets {g['nets']}" for g in group]
    return "\n".join(lines) + "\n"
