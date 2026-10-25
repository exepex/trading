"""EDGE2 F1 (protocol `research/edge2/F1_PROTOCOL.md`): the discovery run on NIFTY and BANKNIFTY weeklies, then, once,
the held-out read of the nominated variants on FINNIFTY and MIDCPNIFTY. Exploratory: it can nominate, never prove.

    python research/edge2/study.py discovery   # writes research/edge2/f1/discovery.json (commit it)
    python research/edge2/study.py heldout     # only after discovery.json is committed; writes heldout.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(HERE), str(ROOT / "research" / "edge1")]

from edge1study.stt_history import charges_on  # noqa: E402
from f1study import report, seal, summary  # noqa: E402
from f1study.cycles import weekly_cycles  # noqa: E402
from f1study.inputs import IndexCloses, cycle_inputs  # noqa: E402
from f1study.trades import STRUCTURES, run_structure  # noqa: E402

OUT = HERE / "f1"
FIRST_DAY, WARM_UP_FROM = date(2019, 1, 1), date(2018, 1, 1)
PERIODS = {"NIFTY": (FIRST_DAY, date(2026, 10, 9)), "BANKNIFTY": (FIRST_DAY, date(2024, 11, 13)),
           "FINNIFTY": (FIRST_DAY, date(2024, 11, 30)), "MIDCPNIFTY": (FIRST_DAY, date(2024, 11, 30))}  # fmt: skip
TRIALS = dict(zip([summary.variant_name(c, g) for c in STRUCTURES for g in ("G0", "G12", "G15")], range(109, 115)))
PADS = (1.0, 2.0)


def code_hash() -> str:
    files = sorted((HERE / "f1study").glob("*.py")) + [Path(__file__)]
    return hashlib.sha256(b"".join(f.read_bytes() for f in files)).hexdigest()


def head_commit() -> str:
    return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def regular_sessions(first: date, last: date) -> list[date]:
    from fno.storage.wiring import build_session_calendar

    cal = build_session_calendar()
    return [d for d in cal.sessions(first, last) if cal.session_kind(d) == "regular"]


def discovery_closes(symbol: str) -> dict[date, float]:
    from fno.price_ranges import wiring as g13b

    closes = g13b.build_closes(g13b.build_tables(g13b.build_store()))
    return {v.day: v.value for v in closes.closes(symbol) if v.day >= WARM_UP_FROM}


def held_out_closes(symbol: str, days: list[date]) -> dict[date, float]:
    from fno.fo_bhavcopy import INDEX_NAMES, BadFile, read_index_closes
    from fno.storage.wiring import build_stored_index_close_files

    files, found = build_stored_index_close_files(), {}
    for day in days:
        name, data = files.get(day)
        try:
            value = read_index_closes(data, name).get(INDEX_NAMES[symbol]) if data else None
        except BadFile:
            value = None
        if value:
            found[day] = value
    return found


def runs_for(inputs, charges) -> dict:
    hist = charges_on(charges)
    return {code: {"pad1": run_structure(code, inputs, charges, PADS[0]),
                   "pad2": run_structure(code, inputs, charges, PADS[1]),
                   "hist": run_structure(code, inputs, charges, PADS[0], hist)} for code in STRUCTURES}  # fmt: skip


def index_inputs(symbols, closes_of, held_out_open: bool, schedule=None):
    from f1study.files import cached_rows

    seal.allowed(symbols, held_out_open)
    days = regular_sessions(FIRST_DAY, max(PERIODS[s][1] for s in symbols))
    rows = cached_rows(tuple(symbols), days)
    inputs, skips, checks = [], Counter(), []
    for s in symbols:
        first, last = PERIODS[s]
        cycles = weekly_cycles(s, rows[s], days, first, last)
        kwargs = {} if schedule is None else {"schedule": schedule}
        found, skipped, checked = cycle_inputs(cycles, rows[s], IndexCloses.of(closes_of(s)), **kwargs)
        inputs += found
        skips.update(f"{s}:{k.reason}" for k in skipped)
        checks += checked
    return inputs, skips, checks


def run(mode: str, symbols, closes_of, held_out_open: bool, extra: dict, schedule=None) -> dict:
    from fno.config import load_app_config

    inputs, skips, checks = index_inputs(symbols, closes_of, held_out_open, schedule)
    rows = summary.family(runs_for(inputs, load_app_config()["charges"]))
    return {"mode": mode, "exploratory": True, "protocol": "research/edge2/F1_PROTOCOL.md", "head": head_commit(),
            "code_sha256": code_hash(), "trials": TRIALS, "symbols": list(symbols), "tradeable_cycles": len(inputs),
            "skipped_cycles": dict(sorted(skips.items())),
            "settlement_checks": {"checked": len(checks), "disagree": [e for e, ok in checks if not ok]},
            "variants": rows, **extra}  # fmt: skip


def inputs_check() -> int:
    """The discovery cycles' counts and skip reasons only: no trade is priced and no settlement is compared."""
    inputs, skips, checks = index_inputs(seal.DISCOVERY_SYMBOLS, discovery_closes, False)
    by_index = Counter(i.cycle.index for i in inputs)
    print(
        json.dumps(
            {
                "tradeable": dict(by_index),
                "skipped": dict(sorted(skips.items())),
                "settlement_checks": len(checks),
                "settlement_disagree": sum(not ok for _, ok in checks),
            }
        )
    )
    return 0


def discovery() -> dict:
    result = run("discovery", seal.DISCOVERY_SYMBOLS, discovery_closes, False, {})
    result["nominated"] = summary.nominated(result["variants"])
    return result


def held_out() -> dict:
    from f1study.held_out_lots import held_out_lot

    nominees = seal.nominated_for_held_out(ROOT, OUT / "discovery.json")
    days = regular_sessions(WARM_UP_FROM, PERIODS["FINNIFTY"][1])
    result = run("heldout", seal.HELD_OUT_SYMBOLS, lambda s: held_out_closes(s, days), True,
                 {"nominated": nominees}, held_out_lot)  # fmt: skip
    p = {n: result["variants"][n]["p"] for n in nominees}
    holm = summary.stats.holm_family(p)
    result["passed"] = [n for n in nominees if holm[n] and (result["variants"][n]["mean_net_pad2"] or 0) > 0]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("discovery", "heldout", "inputs"))
    mode = parser.parse_args().mode
    if mode == "inputs":
        return inputs_check()
    result = discovery() if mode == "discovery" else held_out()
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{mode}.json"
    path.write_text(json.dumps(result, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    (OUT / f"{mode}_tables.md").write_text(report.tables(result), encoding="utf-8")
    print(f"{path.relative_to(ROOT)}: nominated {result['nominated']}" + (
        f", passed {result['passed']}" if mode == "heldout" else ""))  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
