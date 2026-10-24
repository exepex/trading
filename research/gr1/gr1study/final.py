"""Run 2's decision (protocol section 10): each cell's selected winner on the final period, never refitted. Sharper
needs a negative paired QS difference with Holm-adjusted two-sided p < 0.05 across the cells that have a winner,
both calibration bands, no crossing, no input gap over 5% and a smaller median 90% width. Every candidate's final
numbers are reported too; only the winner is decided on."""

from __future__ import annotations

from collections.abc import Sequence

from fno.forecast_scoring.block_bootstrap import compare, holm_significant
from fno.price_ranges.scores import comparison_seed

from .candidates import Context
from .evaluate import numbers
from .rows import Row
from .selection import GAP_LIMIT, bands_ok, candidate_for
from .splits import c9_split

KNOWN_BEFORE = ("C1", "C2")  # judge 428: their final look re-measures the finding that suggested them
NOT_SHOWN = "not shown at this sample size"
SHARPER, NOT_SHARPER = "sharper (exploratory)", "not sharper"


def final_cell(cell: tuple[str, str], chosen: dict, rows: Sequence[Row], ctx: Context) -> dict:
    c0 = numbers(None, None, rows, ctx)
    fitted = {cid: e for cid, e in chosen["candidates"].items() if e["status"] == "fitted"}
    every = {
        cid: numbers(candidate_for(cid, e["scales"]), e["theta"], rows, ctx).as_dict() for cid, e in fitted.items()
    }
    result = {"c0": dict(c0.as_dict(), bands_ok=bands_ok(c0)), "every_candidate": every, "winner": chosen["winner"]}
    if "C9" in fitted:  # SF3: the split is part of the frozen output, never computed after the look
        result["c9_split"] = c9_split(cell[0], candidate_for("C9", fitted["C9"]["scales"]), fitted["C9"]["theta"], rows,
                                      ctx)  # fmt: skip
    winner = chosen["winner"]
    if winner is None:
        return dict(result, verdict=NOT_SHOWN)
    entry = chosen["candidates"][winner]
    n = numbers(candidate_for(winner, entry["scales"]), entry["theta"], rows, ctx)
    test = compare(list(n.differences), comparison_seed("GR1", *cell, winner))
    return dict(result, winner_numbers=n.as_dict(), p_value=test.p_value, tested=test.tested,
                interval_unadjusted_95=test.interval, mean_difference=test.mean_difference,
                checks={"bands_ok": bands_ok(n), "crossed": n.crossed, "gap_ok": n.dropped_share <= GAP_LIMIT,
                        "narrower_90": n.width_90 is not None and c0.width_90 is not None
                        and n.width_90 < c0.width_90},
                known_before_the_study=winner in KNOWN_BEFORE)  # fmt: skip


def decide(cells: dict[str, dict]) -> dict[str, dict]:
    """Holm across the cells that have a winner (at most 4), then every check."""
    tested = [k for k, c in cells.items() if c["winner"] is not None]
    significant = dict(zip(tested, holm_significant([cells[k]["p_value"] for k in tested]), strict=True))
    for key, cell in cells.items():
        if cell["winner"] is None:
            continue
        checks = cell["checks"]
        ok = (significant[key] and cell["tested"] and cell["mean_difference"] is not None
              and cell["mean_difference"] < 0 and checks["bands_ok"] and not checks["crossed"]
              and checks["gap_ok"] and checks["narrower_90"])  # fmt: skip
        cell["holm_significant"] = significant[key]
        cell["verdict"] = SHARPER if ok else NOT_SHARPER
    return cells
