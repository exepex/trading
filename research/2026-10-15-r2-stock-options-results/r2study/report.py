"""`results.json` and `results.md` (PROTOCOL.md section 11): the stage reached, the answer and every number named."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date

from .rules import ASSUMED_HURDLE, MIN_CLUSTERS_A_YEAR, clusters_a_year_needed
from .spreads import SpreadModel

TRIAL = 53


def plain(value):
    """JSON-ready copy: dataclasses as dicts, dates as text, tuple keys joined, floats rounded to 6 places."""
    if isinstance(value, SpreadModel):
        return {"tercile_bounds": list(value.bounds), "buckets": [plain(b) for b in value.distinct()]}
    if is_dataclass(value):
        return plain(asdict(value))
    if isinstance(value, dict):
        return {(" ".join(map(str, k)) if isinstance(k, tuple) else str(k)): plain(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [plain(v) for v in value]
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return round(value, 6)
    return value


def results_json(results: dict, trials_total: int, run_commit: str) -> dict:
    out = plain(results)
    out["trial"] = f"trial {TRIAL} of {trials_total}"
    out["run_commit"] = run_commit
    out["assumed_hurdle"] = ASSUMED_HURDLE
    out["clusters_a_year_rule"] = {"registered": MIN_CLUSTERS_A_YEAR, "power_80": clusters_a_year_needed(0.842)}
    return out


def _fmt(value, pattern: str = "{:,.0f}") -> str:
    return "n/a" if value is None else pattern.format(value)


def structure_rows(structures: list[dict]) -> list[str]:
    rows = [
        "| Structure | Events | Fit cap, no pads | Fit + liquid | Fit + liquid, pads | Median EN (Rs) | Mean EN (Rs) |"
        " Median e* | Clusters/yr | Kish (passing) | First failed |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in structures:
        rows.append(
            f"| {s['name']} | {s['events']} | {s['stage1_share']:.1%} | {s['stage2_share']:.1%} | "
            f"{_fmt(s['stage3_share'], '{:.1%}')} | {_fmt(s['median_net'])} | {_fmt(s['mean_net'])} | "
            f"{_fmt(s['median_break_even'], '{:.1%}')} | {_fmt(s['clusters_a_year'], '{:.1f}')} | "
            f"{_fmt(s['kish_passing'], '{:.1f}')} | {s['first_failed'] or 'none'} |"
        )
    return rows


def results_markdown(out: dict) -> str:
    answer = out["answer"]
    zero = out["stage0"]
    corr = out["correlation"]
    lines = [
        "# R2 results: stock options around results (feasibility)",
        "",
        f"**Answer: {answer['answer']}** ({answer['stage']}{'; ' + answer['reason'] if answer.get('reason') else ''}). "
        f"{out['trial']}. Run commit `{out['run_commit']}`. Window {out['window'][0]} to {out['window'][1]}.",
        "",
        f"e = {out['assumed_hurdle']:.0%} is the **assumed hurdle** (reasoning only, not a conservative bound); "
        "e* is the break-even edge. Clusters a year: registered rule "
        f"{out['clusters_a_year_rule']['registered']} (decides); 80%-power need "
        f"{out['clusters_a_year_rule']['power_80']} (shown only).",
        "",
        "## Stage 0",
        "",
        f"- Results-date coverage: {zero['coverage']['covered']} of {zero['coverage']['stock_quarters']} "
        f"stock-quarters ({zero['coverage']['share']:.1%}); lot unknown: {zero['lot_unknown_share']:.1%} of "
        "decision-window events.",
        f"- Legacy lot derivation: {zero['lot_validation']['exact_matches']} of "
        f"{zero['lot_validation']['stock_sessions']} exact ({zero['lot_validation']['share']:.1%}); "
        f"valid: {zero['lot_validation']['valid']}.",
        f"- Events: {json.dumps(out['events'])}",
        "",
        "## Decision window (1 Oct 2024 on)",
        "",
        *structure_rows(out["structures"]),
        "",
        "## 2019 - Sep 2024 (descriptive, never decides)",
        "",
        *structure_rows(out["structures_2019_sep_2024"]),
        "",
        "## Within-week correlation (2019-2021 events only)",
        "",
        f"- {corr['events']} events in {corr['clusters']} clusters; ICC of m: {_fmt(corr['rho_move'], '{:.3f}')} "
        f"(90% {corr['rho_move_interval']}); ICC of |m|: {_fmt(corr['rho_abs'], '{:.3f}')} "
        f"(90% {corr['rho_abs_interval']}); Kish effective count {corr['kish']:.1f}.",
        f"- Decision-window events analysed: {json.dumps(out['decision_kish_all'])}",
        "",
        "## Descriptive",
        "",
        "```json",
        json.dumps(out["descriptive"], indent=1),
        "```",
        "",
        "## Spread buckets (one Groww snapshot; depth descriptive only)",
        "",
        "```json",
        json.dumps(out["spreads"], indent=1),
        "```",
    ]
    return "\n".join(lines) + "\n"
