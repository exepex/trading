"""EDGE1, simple rule-based option trades after real costs (protocol `research/edge1/PROTOCOL.md`). Research only.

    python research/edge1/study.py --select   # run 1: 2019-22, G1; writes selection.json (commit it)
    python research/edge1/study.py --final    # run 2: 2023-26 once, G1 passers only; writes final.json

Both refuse unless every study file matches FREEZE.md and the folder is clean; run 2 also refuses unless
selection.json is committed and no final.json ever existed (protocol section 13)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from edge1study import guard  # noqa: E402
from edge1study.inputs import LAST_FILE_DAY  # noqa: E402
from edge1study.runner import RUN1_SEAL, RUN2_FROM  # noqa: E402

SELECTION, FINAL_FILE = ROOT / "research/edge1/selection.json", ROOT / "research/edge1/final.json"
SPAN_WORKERS = 8


def encode(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, indent=1, default=str) + "\n"


def margin_reader():
    """(index, trades) -> each taken trade's entry margin, SPAN files read once per day through A14's prefetch."""
    from edge1study.margin import manifest, span_on, trade_margins

    from fno.nse_margins.prefetch import in_order, per_thread
    from fno.nse_margins.wiring import build_drive_span_files

    sha256, cache = manifest(), {}

    def margins(index: str, trades):
        days = sorted({t.cycle.entry_day for t in trades if t.taken} - {d for (i, d) in cache if i == index})
        files = dict(in_order(per_thread(build_drive_span_files), days, SPAN_WORKERS))
        for day in days:
            cache[(index, day)] = span_on(lambda d: files[d], day, sha256, index)
        return trade_margins(trades, {d: cache[(index, d)] for (i, d) in cache if i == index})

    return margins


def expected_run2_cycles() -> int:
    """Run 2's monthly cycles as calendar months (one expiry a month from Feb 2023 to the last file day's month), so
    run 1 reads no run-2 data; advisory only (judge 468 note 1)."""
    first, last = RUN2_FROM.replace(month=2), LAST_FILE_DAY
    return (last.year - first.year) * 12 + last.month - first.month


def last_days(markets) -> dict:
    return {index: market.days[-1] for index, market in markets.items()}


def run_select() -> dict:
    from edge1study.inputs import calendar, markets
    from edge1study.runs import run1

    from fno.config import load_app_config

    found, cal = markets(through=RUN1_SEAL), calendar()
    run2_cycles = dict.fromkeys(found, expected_run2_cycles())
    return {"run": "run1", "variants": run1(found, cal, load_app_config()["charges"], margin_reader(), run2_cycles),
            "run2_cycles": run2_cycles}  # fmt: skip


def run_final(selection: dict) -> dict:
    from edge1study.inputs import calendar, markets
    from edge1study.runs import run2

    from fno.config import load_app_config

    found = markets()
    return {"run": "run2", **run2(found, calendar(), load_app_config()["charges"], margin_reader(),
                                  selection["variants"], last_days(found))}  # fmt: skip


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--select", action="store_true")
    group.add_argument("--final", action="store_true")
    args = parser.parse_args()
    try:
        guard.check_code(ROOT)
        if args.final:
            guard.check_final_allowed(ROOT)
    except guard.Refused as refused:
        print(f"REFUSED: {refused}")
        return 1
    if args.select:
        SELECTION.write_text(encode(run_select()), encoding="utf-8")
        print(f"selection written: {SELECTION.relative_to(ROOT)} (commit it before --final)")
    else:
        FINAL_FILE.write_text(encode(run_final(json.loads(SELECTION.read_text(encoding="utf-8")))), encoding="utf-8")
        print(f"final written: {FINAL_FILE.relative_to(ROOT)} (commit it; run 2 is now read)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
