"""`results.md` from the results (PROTOCOL.md sections 8-15 and 20). Every figure is labelled exploratory measurement.
A cell that cannot be read prints its status, never a number. From option P&L only the two flip shares are printed."""

from __future__ import annotations

from .bootstrap import BLOCKS
from .cells import OK
from .entries import main_width
from .figures import SPLITS

SHOWN_BLOCK = BLOCKS[0]
LABEL = "Exploratory measurement: no edge, no strategy verdict; option prices of 2024-26 are spent data."
NOT_MEASURED = (
    "What waiting costs in the decision itself (an older signal): not measured.",
    "The spread at the fill times: not measured (only A4's 15:00 spread, as an order of size, below).",
    "What the 14:00 path gives up (the last hour's information): not measured.",
    "Candle closes are last trades, not the bid or ask the owner would get; the live follow-up after 20 A16 sessions "
    "can confirm or reject these figures.",
)


def _n(value: float | None, digits: int = 1) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def _pct(value: float | None) -> str:
    return "-" if value is None else f"{value:.0%}"


def _interval(pair) -> str:
    return f"[{pair[0]:.1f}, {pair[1]:.1f}]"


def _main_row(cell: dict) -> str:
    left = sum(cell["left_out"].values())
    head = f"| {cell['cell']}{' (= E4 15:15)' if cell['e4_snapshot'] else ''} | {cell['n']} | {left} |"
    if cell["status"] != OK:
        return f"{head} {cell['status']} |" + " |" * 6
    shares = " / ".join(_pct(v) for v in cell["share_above"].values())
    timed = cell["time_part"]
    return (f"{head} {_n(cell['p10_c'])} / {_n(cell['p50_c'])} / {_n(cell['p90_c'])} | {_n(cell['mean_abs_c'])} "
            f"{_interval(cell['mean_abs_c_interval'][SHOWN_BLOCK])} | {shares} | {_n(cell['mean_c'])} | "
            f"{_n(timed['mean_c'])} vs {_n(timed['mean_time_part'])} ({timed['not_computed']} not computed) | "
            f"{_n(cell['rupees']['mean_abs_c'], 0)} |")  # fmt: skip


def _main_table(cells: list[dict]) -> list[str]:
    return [
        "| Cell | n | Left out | C p10 / p50 / p90 (points) | Mean abs C [95%] | C above 5% / 10% / 20% of risk "
        "| Mean C | Mean C vs time part | Mean abs C, Rs a lot |",
        "|---|---|---|---|---|---|---|---|---|",
        *(_main_row(c) for c in cells),
    ]


def _sensitivity(cells: list[dict]) -> list[str]:
    lines = ["| Cell | n | Mean abs C [95%] | C above 5% / 10% / 20% of risk |", "|---|---|---|---|"]
    for c in cells:
        if c["status"] != OK:
            lines.append(f"| {c['cell']} | {c['n']} | {c['status']} | |")
            continue
        shares = " / ".join(_pct(v) for v in c["share_above"].values())
        interval = _interval(c["mean_abs_c_interval"][SHOWN_BLOCK])
        lines.append(f"| {c['cell']} | {c['n']} | {_n(c['mean_abs_c'])} {interval} | {shares} |")
    return lines


def _paired(rows: list[dict]) -> list[str]:
    lines = ["| Family | n | Mean D (points) [95%] |", "|---|---|---|"]
    for r in rows:
        shown = f"{_n(r['mean_d'])} {_interval(r['interval'][SHOWN_BLOCK])}" if r["status"] == OK else r["status"]
        lines.append(f"| {r['cell']} | {r.get('n', '-')} | {shown} |")
    return lines


def _flip_share(value: dict | None) -> str:
    return "-" if value is None else f"{value['share']:.1%} [{value['interval'][0]:.1%}, {value['interval'][1]:.1%}]"


def _flips(rows: list[dict]) -> list[str]:
    lines = ["| Cell | Bad flips (share of wins) [95%] | Good flips (share of losses) [95%] | Expiries | Not settled |",
             "|---|---|---|---|---|"]  # fmt: skip
    for r in rows:
        if r["status"] != OK:
            lines.append(f"| {r['cell']} | {r['status']} | | | |")
            continue
        lines.append(f"| {r['cell']} | {_flip_share(r['bad_flip_share'])} | {_flip_share(r['good_flip_share'])} | "
                     f"{r['expiries']} | {r['not_settled']} |")  # fmt: skip
    return lines


def _band(figures: dict) -> str:
    if "mean_abs_c" not in figures:
        return f"{figures.get('status', 'counted')} (n {figures['n']})"
    shown = f"{_n(figures['mean_abs_c'])}, p50 {_n(figures['p50_c'])}, >10% {_pct(figures['share_above_10pct'])}"
    return f"{shown} (n {figures['n']})"


def _splits(cells: list[dict]) -> list[str]:
    lines = []
    for name in SPLITS:
        lines += ["", f"### {name}: mean abs C, median C, share above 10% of risk (n)", ""]
        for cell in cells:
            if cell["status"] == OK:
                bands = "; ".join(f"{band}: {_band(f)}" for band, f in cell["splits"][name].items())
                lines.append(f"- {cell['cell']}: {bands}")
    return lines


def _spreads(caveat: dict) -> list[str]:
    lines = [f"A4 days used: {caveat['a4_days']}. Entry spread, points per unit (legs x band median half-spread):"]
    lines += [f"- {family}: {_n(f['entry_spread_points'], 2)} ({f['legs']} legs, band {f['band']})"
              for family, f in caveat["families"].items()]  # fmt: skip
    return lines


def render(results: dict) -> str:
    analysis = results["analysis"]
    main = [c for c in analysis["cells"] if c["width"] == main_width(c["family"])]
    extra = [c for c in analysis["cells"] if c["width"] != main_width(c["family"])]
    lines = [f"# FT1 results: fill timing (story E8a, ledger trial {results['trial']})", "", f"**{LABEL}**", "",
             f"Window: {results['window']}. Lot: {results['lot']} units. Run commit: `{results['run_commit']}`.", "",
             "## What this cannot measure", "", *(f"- {line}" for line in NOT_MEASURED), "",
             "## Days left out", "", *(f"- {k}: {v}" for k, v in results["days_left_out"].items()), "",
             "## Entry move C per family, decision time and R (main width)", "",
             "`C = V_fill - V_decision`, points per unit; positive is worse for the trader. Mean C is mostly time "
             "decay and is never the cost of waiting.", "", *_main_table(main), "",
             "## The owner's choice: D = bad-side C at 15:00 minus at 14:00, R = 60", "", *_paired(analysis["paired"]),
             "", "## Flip share at R = 60 (held to expiry, net of charges)", "", *_flips(analysis["flips"]), "",
             "## Width sensitivity (15:00, R = 60): mean abs C and threshold shares only", "", *_sensitivity(extra),
             "", "## Splits", *_splits(main), "", "## Spread caveat (order of size only)", "",
             *_spreads(results["spreads"]), "",
             "Hand-check days (story criterion 2): `hand_check` in results.json.", ""]  # fmt: skip
    return "\n".join(lines)
