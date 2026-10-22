"""GR1, sharper price ranges (protocol `research/gr1/PROTOCOL.md`, ledger trials 56-70). Research only, read-only.

    python research/gr1/study.py --select   # run 1: fit on train, select on 2024; writes selection.json
    python research/gr1/study.py --final    # run 2: the final period once, from the committed selection.json

Both refuse unless every study file matches FREEZE.md and the folder is clean; run 2 also refuses unless
selection.json is committed and no final.json ever existed (protocol section 12)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gr1study import guard, inputs  # noqa: E402
from gr1study.cues import OPEN_CUTOFF  # noqa: E402
from gr1study.final import decide, final_cell  # noqa: E402
from gr1study.n0 import n0_candidates, n0_pairs, n0_report, n0_study  # noqa: E402
from gr1study.periods import FINAL, SELECT, TRAIN  # noqa: E402
from gr1study.rows import implied_rows  # noqa: E402
from gr1study.selection import select_cell  # noqa: E402

CELLS = (("NIFTY", "N1"), ("NIFTY", "N3"), ("BANKNIFTY", "N1"), ("BANKNIFTY", "N3"))
SELECTION, FINAL_FILE = ROOT / "research/gr1/selection.json", ROOT / "research/gr1/final.json"


def encode(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, indent=1, default=str) + "\n"


def records_sha256(records: list[dict]) -> str:
    return hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()


def by_period(rows, cell):
    cell_rows = [r for r in rows if r.cell == cell]
    return {p: [r for r in cell_rows if r.period == p] for p in (TRAIN, SELECT, FINAL)}


def n0_inputs(rows, last_day):
    opens = inputs.up_to(inputs.opens(min(r.day for r in rows), last_day), last_day)
    gaps = {r.target_day: math.log(opens[r.target_day] / r.s_ref)
            for r in rows if r.underlying == "NIFTY" and r.horizon == "N1" and r.target_day in opens}  # fmt: skip
    return opens, gaps


def run_select() -> dict:
    from fno.storage.wiring import build_session_calendar

    records = inputs.back_fill_records()
    rows = implied_rows(records, inputs.closes(), final_open=False)
    ctx = inputs.context(rows, build_session_calendar())
    cells = {}
    for cell in CELLS:
        periods = by_period(rows, cell)
        cells["/".join(cell)] = select_cell(cell[0], periods[TRAIN], periods[SELECT], ctx)
    opens, gaps = n0_inputs(rows, max(r.day for r in rows))
    candidates = n0_candidates(gaps, lambda d: ctx.cue_move("sp500", d, OPEN_CUTOFF))
    pairs = n0_pairs(rows, opens, final_open=False)
    split = {p: [pr for pr in pairs if pr[0].period == p] for p in (TRAIN, SELECT)}
    study = n0_study(split, ctx, candidates)
    study["select_report"] = n0_report(split[SELECT], study, ctx, candidates, "select")
    return {"protocol": "research/gr1/PROTOCOL.md", "records_sha256": records_sha256(records),
            "train_median_ln_vix": ctx.train_median_ln_vix, "train_vix_terciles": ctx.train_vix_terciles,
            "cells": cells, "n0": study}  # fmt: skip


def run_final(selection: dict) -> dict:
    from fno.storage.wiring import build_session_calendar

    records = inputs.back_fill_records()
    rows = implied_rows(records, inputs.closes(), final_open=True)
    stats = (selection["train_median_ln_vix"], tuple(selection["train_vix_terciles"]))
    ctx = inputs.context(rows, build_session_calendar(), stats)
    cells = {}
    for cell in CELLS:
        key = "/".join(cell)
        cells[key] = final_cell(cell, selection["cells"][key], by_period(rows, cell)[FINAL], ctx)
    opens, gaps = n0_inputs(rows, max(r.day for r in rows))
    candidates = n0_candidates(gaps, lambda d: ctx.cue_move("sp500", d, OPEN_CUTOFF))
    pairs = [pr for pr in n0_pairs(rows, opens, final_open=True) if pr[0].period == FINAL]
    n0 = n0_report(pairs, selection["n0"], ctx, candidates, "final")
    return {"records_sha256": records_sha256(records), "selection_sha256": hashlib.sha256(SELECTION.read_bytes())
            .hexdigest(), "cells": decide(cells), "n0": dict(n0, carried=selection["n0"]["winner"])}  # fmt: skip


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--select", action="store_true")
    action.add_argument("--final", action="store_true")
    args = parser.parse_args(argv)
    try:
        guard.check_code(ROOT)
        if args.final:
            guard.check_final_allowed(ROOT)
            FINAL_FILE.write_text(encode(run_final(json.loads(SELECTION.read_text()))))
            print(f"final written: {FINAL_FILE.relative_to(ROOT)} (commit it; the final period is now read)")
        else:
            SELECTION.write_text(encode(run_select()))
            print(f"selection written: {SELECTION.relative_to(ROOT)} (commit it before --final)")
    except guard.Refused as refusal:
        print(f"REFUSED: {refusal}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
