"""EDGE2 F8 (protocol `research/edge2/F8_PROTOCOL.md`): the FII-change lean as the side of a 2-leg NIFTY weekly credit
spread. Discovery (2019-24) measures the spread alone, both sides; the held-out read (2025-26, once, after a judge)
tests the filter. Exploratory: it can nominate, never prove.

    python research/edge2/study_f8.py discovery   # writes research/edge2/f8/discovery.json (commit it)
    python research/edge2/study_f8.py heldout     # once, after the judge, for the variants discovery kept
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(HERE), str(ROOT / "research" / "edge1")]

from f1study.cycles import TAKEN_CYCLE, weekly_cycles  # noqa: E402
from f1study.seal import SealBroken, nominated_for_held_out  # noqa: E402
from f1study.trades import lot_of  # noqa: E402
from f8study import summary  # noqa: E402
from f8study.entries import cached_entries, forward_at_open  # noqa: E402
from f8study.spreads import CALL, PUT, VARIANTS, as_quotes, spread_trade  # noqa: E402

OUT = HERE / "f8"
DISCOVERY = (date(2019, 1, 1), date(2024, 12, 31))
HELD_OUT = (date(2025, 1, 1), date(2026, 10, 6))
TRIALS = dict(zip([f"EDGE2-F8-{v}" for v in VARIANTS], range(121, 124)))


def code_hash() -> str:
    files = sorted((HERE / "f8study").glob("*.py")) + [Path(__file__)]
    return hashlib.sha256(b"".join(f.read_bytes() for f in files)).hexdigest()


def market():
    """F1's cached NIFTY rows and sessions (the same cache key as F1's run) and NIFTY's closes."""
    import study as f1
    from f1study.files import cached_rows

    symbols = ("NIFTY", "BANKNIFTY")
    days = f1.regular_sessions(f1.FIRST_DAY, max(f1.PERIODS[s][1] for s in symbols))
    rows = cached_rows(symbols, days)["NIFTY"]
    return rows, days, f1.discovery_closes("NIFTY")


def cycle_inputs(period: tuple[date, date], held_out_open: bool) -> list[dict]:
    if period[1] > DISCOVERY[1] and not held_out_open:
        raise SealBroken("held-out cycles requested before the held-out read was opened")
    rows, days, closes = market()
    by_day = {r.day: r for r in rows}
    cycles = [c for c in weekly_cycles("NIFTY", rows, days, *period) if c.status == TAKEN_CYCLE]
    quotes = cached_entries([(c.entry_day, c.expiry) for c in cycles])
    found = []
    for c in cycles:
        entry = quotes[(c.entry_day, c.expiry)]
        previous, level = closes.get(c.previous_expiry), closes.get(c.expiry)
        forward = forward_at_open(entry, previous) if previous else None
        lot = lot_of("NIFTY", by_day[c.entry_day].lots, by_day[c.entry_day].source, c.expiry)
        found.append({"cycle": c, "quotes": entry, "forward": forward, "lot": lot, "settlement": level})
    return found


def priced(inputs: list[dict], variant: str, side: str, pad: float, at_open: bool, charges) -> list[dict]:
    rows = []
    for x in inputs:
        c = x["cycle"]
        base = {"cycle": c.expiry.isoformat(), "side": side}
        if x["forward"] is None or not x["lot"] or x["settlement"] is None:
            rows.append({**base, "status": "no_entry_inputs", "net": 0.0})
            continue
        t = spread_trade(variant, side, c.entry_day, c.expiry, as_quotes(x["quotes"], c.expiry, at_open), x["forward"],
                         x["lot"], x["settlement"], charges, pad)  # fmt: skip
        rows.append({**base, "status": t.status, "gross": t.gross, "charges": t.charges, "pads": t.pads, "net": t.net,
                     "credit": t.credit,
                     "width": abs(t.legs[0].strike - t.legs[1].strike) if t.legs else None})  # fmt: skip
    return rows


def header(mode: str) -> dict:
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return {"mode": mode, "exploratory": True, "protocol": "research/edge2/F8_PROTOCOL.md", "head": head,
            "code_sha256": code_hash(), "trials": TRIALS}  # fmt: skip


def discovery() -> dict:
    from fno.config import load_app_config

    charges, inputs = load_app_config()["charges"], cycle_inputs(DISCOVERY, False)
    rows = {}
    for v in VARIANTS:
        run = {key: {s: priced(inputs, v, s, pad, at_open, charges) for s in (PUT, CALL)}
               for key, pad, at_open in (("pad1", 1.0, True), ("pad2", 2.0, True), ("close", 1.0, False))}  # fmt: skip
        rows[f"EDGE2-F8-{v}"] = summary.discovery_row(run["pad1"], run["pad2"], run["close"])
    kept = [n for n, r in rows.items() if not r["futile"]]
    return {**header("discovery"), "cycles": len(inputs), "variants": rows, "nominated": kept}


def held_out() -> dict:
    from f6study.data import oi_nets

    from fno.config import load_app_config
    from fno.storage import wiring

    nominees = nominated_for_held_out(ROOT, OUT / "discovery.json")
    charges, inputs = load_app_config()["charges"], cycle_inputs(HELD_OUT, True)
    _, days, _ = market()
    from fno.storage.raw_library import StoredFilesLibrary

    library = StoredFilesLibrary(wiring._reader_raw_stores())
    oi_files = wiring.daily_files("participant-oi", wiring.ParticipantOiSource, library)
    sides = {}
    for x in inputs:
        t = x["cycle"].previous_expiry
        before = days[days.index(t) - 1]
        today, earlier = oi_nets(t, oi_files)[0], oi_nets(before, oi_files)[0]
        change = None if today is None or earlier is None else today - earlier
        sides[x["cycle"].expiry.isoformat()] = None if not change else (PUT if change > 0 else CALL)
    rows = {}
    for name in nominees:
        v = name.removeprefix("EDGE2-F8-")
        both = {pad: {s: priced(inputs, v, s, pad, True, charges) for s in (PUT, CALL)} for pad in (1.0, 2.0)}
        pairs = [(p, c) for p, c in zip(both[1.0][PUT], both[1.0][CALL], strict=True) if sides[p["cycle"]]]
        chosen = {pad: [p if sides[p["cycle"]] == PUT else c
                        for p, c in zip(both[pad][PUT], both[pad][CALL], strict=True) if sides[p["cycle"]]]
                  for pad in (1.0, 2.0)}  # fmt: skip
        rows[name] = summary.held_out_row(chosen[1.0], chosen[2.0], pairs)
    return {**header("heldout"), "cycles": len(inputs), "no_signal": sum(s is None for s in sides.values()),
            "variants": rows, "nominated": nominees, "passed": summary.verdicts(rows)}  # fmt: skip


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("discovery", "heldout"))
    mode = parser.parse_args().mode
    result = discovery() if mode == "discovery" else held_out()
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{mode}.json"
    path.write_text(json.dumps(result, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"{path.relative_to(ROOT)}: kept for the held-out read {result['nominated']}" + (
        f", passed {result['passed']}" if mode == "heldout" else ""))  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
