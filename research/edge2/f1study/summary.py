"""Each F1 variant's figures, the family's Holm and the nomination to the held-out read (protocol section 8). Inputs
are each structure's trade rows (`trades.trade_row`) at the decided Rs 1 pad, at the Rs 2 pad and with historical
STT, over the same cycles."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence

from . import stats
from .gate import GATES
from .trades import STRUCTURES

NOMINATED_AT_MOST, GATE_P_MAX = 2, 0.10
REGIME_FROM = "2024-11-20"  # SEBI's one-weekly-per-exchange rule in force


def gated(rows: Sequence[dict], gate: str) -> list[dict]:
    level = GATES[gate]
    return [r for r in rows if level is None or (r["ratio"] is not None and r["ratio"] >= level)]


def variant_name(code: str, gate: str) -> str:
    return f"EDGE2-F1-{code}-{gate}"


def describe(rows: Sequence[dict], all_rows: Sequence[dict], pad2: Sequence[dict], hist: Sequence[dict],
             gate: str) -> dict:  # fmt: skip
    chosen = gated(rows, gate)
    done = stats.taken(chosen)
    mean, se, clusters = stats.clustered(done)
    nets = [r["net"] for r in done]
    after = [r for r in done if r["index"] == "NIFTY" and r["expiry"] >= REGIME_FROM]
    return {
        "cycles": len(all_rows), "gated": len(chosen), "taken": len(done),
        "skips": dict(Counter(r["status"] for r in chosen if r["status"] != "taken")),
        "mean_gross": stats.mean_of([{**r, "net": r["gross"]} for r in done]),
        "mean_charges": stats.mean_of([{**r, "net": r["charges"]} for r in done]),
        "mean_net": mean, "se": se, "clusters": clusters, "p": stats.one_sided_p(mean, se, clusters),
        "g1_bound": stats.g1_bound(mean, se), "sd": stats.sd_of(done),
        "mean_net_pad2": stats.mean_of(stats.taken(gated(pad2, gate))),
        "mean_net_hist_stt": stats.mean_of(stats.taken(gated(hist, gate))),
        "win_share": sum(n > 0 for n in nets) / len(nets) if nets else None,
        "worst_trade": min(nets) if nets else None, "max_drawdown": stats.drawdown(done),
        "worst_four_weeks": stats.worst_four_weeks(done),
        "by_index": stats.by_key(done, lambda r: r["index"]),
        "by_year": stats.by_key(done, lambda r: r["expiry"][:4]),
        "nifty_after_regime": {"trades": len(after), "mean_net": stats.mean_of(after)},
        "p_gate": None if GATES[gate] is None else stats.random_gate_p(all_rows, len(chosen), mean),
        "sample_plan": stats.sample_plan(stats.sd_of(done), mean),
    }  # fmt: skip


def family(runs: Mapping[str, Mapping[str, list[dict]]]) -> dict[str, dict]:
    """`runs[structure]` = {"pad1": rows, "pad2": rows, "hist": rows}; one row of figures per variant, with Holm."""
    rows = {variant_name(code, gate): describe(runs[code]["pad1"], runs[code]["pad1"], runs[code]["pad2"],
                                               runs[code]["hist"], gate)
            for code in STRUCTURES for gate in GATES}  # fmt: skip
    holm = stats.holm_family({name: r["p"] for name, r in rows.items()})
    for name, r in rows.items():
        r["holm"] = holm[name]
    return rows


def eligible(name: str, r: dict) -> bool:
    each_index = all(v["mean_net"] is not None and v["mean_net"] > 0 for v in r["by_index"].values())
    gate_ok = name.endswith("-G0") or (r["p_gate"] is not None and r["p_gate"] <= GATE_P_MAX)
    pad2 = r["mean_net_pad2"] is not None and r["mean_net_pad2"] > 0
    return r["holm"] and pad2 and bool(r["by_index"]) and each_index and gate_ok


def nominated(rows: Mapping[str, dict]) -> list[str]:
    chosen = [name for name, r in rows.items() if eligible(name, r)]
    return sorted(chosen, key=lambda n: (rows[n]["p"], n))[:NOMINATED_AT_MOST]
