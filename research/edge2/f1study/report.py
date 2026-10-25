"""F1's results tables (protocol section 8) from a run's JSON: one row per variant with its label, every figure
rupees for one lot of the time. The prose around them is written by hand in RESULTS.md."""

from __future__ import annotations


def _rs(value) -> str:
    return "-" if value is None else f"{value:,.0f}"


def _p(value) -> str:
    return "-" if value is None else f"{value:.4f}"


COLUMNS = (
    "Variant (trial)",
    "Gated / taken",
    "Mean gross",
    "Mean charges",
    "Mean net (Rs 1 pad)",
    "SE",
    "One-sided p",
    "Holm",
    "G1 bound",
    "Rs 2 pad",
    "Hist. STT",
    "Win share",
    "Worst trade",
    "Max drawdown",
    "Worst 4 weeks",
    "p_gate (RC1)",
)
HEADER = "| " + " | ".join(COLUMNS) + " |"
RULE = "|" + "---|" * len(COLUMNS)


def variant_line(name: str, trial: int, r: dict) -> str:
    win = "-" if r["win_share"] is None else f"{r['win_share']:.0%}"
    return (f"| {name} ({trial}) | {r['gated']} / {r['taken']} | {_rs(r['mean_gross'])} | {_rs(r['mean_charges'])} | "
            f"{_rs(r['mean_net'])} | {_rs(r['se'])} | {_p(r['p'])} | {'yes' if r['holm'] else 'no'} | "
            f"{_rs(r['g1_bound'])} | {_rs(r['mean_net_pad2'])} | {_rs(r['mean_net_hist_stt'])} | {win} | "
            f"{_rs(r['worst_trade'])} | {_rs(r['max_drawdown'])} | {_rs(r['worst_four_weeks'])} | "
            f"{_p(r['p_gate'])} |")  # fmt: skip


def split_lines(name: str, r: dict) -> list[str]:
    parts = [f"{k} {v['trades']} at {_rs(v['mean_net'])}" for k, v in r["by_index"].items()]
    years = [f"{k}: {_rs(v['mean_net'])} ({v['trades']})" for k, v in r["by_year"].items()]
    after = r["nifty_after_regime"]
    return [f"- **{name}**: by index {'; '.join(parts)}. By year {'; '.join(years)}. NIFTY from 20 Nov 2024: "
            f"{after['trades']} trades at {_rs(after['mean_net'])}. Skips among gated: {r['skips'] or 'none'}. "
            f"Sample plan: {r['sample_plan'] or 'none (mean not positive)'}."]  # fmt: skip


def tables(result: dict) -> str:
    rows = result["variants"]
    lines = [HEADER, RULE] + [variant_line(n, result["trials"][n], rows[n]) for n in sorted(rows)]
    lines += [""] + [line for n in sorted(rows) for line in split_lines(n, rows[n])]
    return "\n".join(lines) + "\n"
