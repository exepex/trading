"""GR1's input probe, before the code freeze (FT1's pattern): counts only. For each cell and period, the implied rows
and the share of days each candidate has its conditioners; also the 09:15 prices for N0. It never reads an outcome
(its close is a constant, so no target close is looked up), never computes a score, and holds no 2025-26 row.

    python research/gr1/probe.py   # writes research/gr1/probe.csv"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from gr1study import inputs  # noqa: E402
from gr1study.candidates import SINGLE  # noqa: E402
from gr1study.periods import SELECT, TRAIN  # noqa: E402
from gr1study.rows import implied_rows  # noqa: E402

CELLS = (("NIFTY", "N1"), ("NIFTY", "N3"), ("BANKNIFTY", "N1"), ("BANKNIFTY", "N3"))
NO_OUTCOME = 1.0  # a constant close: the probe never asks for a real one


def main() -> int:
    from fno.storage.wiring import build_session_calendar

    rows = implied_rows(inputs.back_fill_records(), lambda underlying, day: NO_OUTCOME, final_open=False)
    ctx = inputs.context(rows, build_session_calendar())
    opens = inputs.up_to(inputs.opens(min(r.day for r in rows), max(r.day for r in rows)), max(r.day for r in rows))
    out = []
    for underlying, horizon in CELLS:
        for period in (TRAIN, SELECT):
            cell = [r for r in rows if r.cell == (underlying, horizon) and r.period == period]
            line = {"underlying": underlying, "horizon": horizon, "period": period, "rows": len(cell),
                    "first": min(r.day for r in cell), "last": max(r.day for r in cell)}  # fmt: skip
            for cid, cand in SINGLE.items():
                kept = sum(1 for r in cell if cand.features(r, ctx) is not None)
                line[f"{cid}_days_with_inputs"] = kept
            if horizon == "N1" and underlying == "NIFTY":
                line["n0_targets_with_09_15_price"] = sum(1 for r in cell if r.target_day in opens)
            out.append(line)
    fields = sorted({k for line in out for k in line}, key=lambda k: (k not in ("underlying", "horizon", "period"), k))
    with (HERE / "probe.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)
    print(f"probe written: {len(out)} lines (counts only; no outcome read)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
