"""EDGE2 F6 (protocol `research/edge2/F6_PROTOCOL.md`): participant OI and the next NIFTY futures sessions. Research
only (futures on hold). Exploratory: it can nominate, never prove.

    python research/edge2/study_f6.py inputs      # counts only: files read, signals, no trade priced
    python research/edge2/study_f6.py discovery   # writes research/edge2/f6/discovery.json (commit it)
    python research/edge2/study_f6.py heldout     # once, after the judge, only if discovery nominated a variant
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

from f1study.seal import SealBroken, nominated_for_held_out  # noqa: E402
from f6study import data, summary  # noqa: E402
from f6study.trades import HORIZONS, SIGNALS, FuturesRates, run, stt_on  # noqa: E402

OUT = HERE / "f6"
FIRST_DAY, SEAL_DAY, HELD_OUT_FROM = date(2019, 1, 1), date(2024, 12, 31), date(2025, 1, 1)
TRIALS = dict(zip([f"EDGE2-F6-{s}-{h}" for s in SIGNALS for h in HORIZONS], range(115, 121)))
PADS = (1.0, 2.0)  # index points a unit a side


def code_hash() -> str:
    files = sorted((HERE / "f6study").glob("*.py")) + [Path(__file__)]
    return hashlib.sha256(b"".join(f.read_bytes() for f in files)).hexdigest()


def regular_sessions(first: date, last: date) -> list[date]:
    from fno.storage.wiring import build_session_calendar

    cal = build_session_calendar()
    return [d for d in cal.sessions(first, last) if cal.session_kind(d) == "regular"]


def loaded(last: date, held_out_open: bool) -> list:
    if last > SEAL_DAY and not held_out_open:
        raise SealBroken(f"sessions after {SEAL_DAY} requested before the held-out read was opened")
    return data.sessions(regular_sessions(FIRST_DAY, last))


def family_runs(sessions, exit_by=None, signal_from=None, names=None) -> dict:
    rates = FuturesRates()
    runs = {}
    for name in names or TRIALS:
        signal, horizon = name.split("-")[2:]
        runs[name] = {"pad1": run(signal, horizon, sessions, rates, PADS[0], None, exit_by, signal_from),
                      "pad2": run(signal, horizon, sessions, rates, PADS[1], None, exit_by, signal_from),
                      "hist": run(signal, horizon, sessions, rates, PADS[0], stt_on, exit_by, signal_from)}  # fmt: skip
    return runs


def header(mode: str, sessions) -> dict:
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return {"mode": mode, "exploratory": True, "research_only": "futures on hold (owner, 25 Oct 2026)",
            "protocol": "research/edge2/F6_PROTOCOL.md", "head": head, "code_sha256": code_hash(), "trials": TRIALS,
            "sessions": len(sessions), "oi_missing": sum(s.fii_net is None for s in sessions),
            "futures_missing": sum(not s.futures for s in sessions)}  # fmt: skip


def inputs_check() -> int:
    sessions = loaded(SEAL_DAY, False)
    print(json.dumps(header("inputs", sessions)))
    return 0


def discovery() -> dict:
    sessions = loaded(SEAL_DAY, False)
    rows = summary.family(family_runs(sessions, exit_by=SEAL_DAY))
    return {**header("discovery", sessions), "variants": rows, "nominated": summary.nominated(rows)}


def held_out() -> dict:
    nominees = nominated_for_held_out(ROOT, OUT / "discovery.json")
    sessions = loaded(regular_sessions(HELD_OUT_FROM, date.today())[-1], True)
    rows = summary.family(family_runs(sessions, signal_from=HELD_OUT_FROM, names=nominees))
    holm = summary.holm([rows[n]["p"] for n in nominees], summary.ALPHA)
    passed = [n for n, ok in zip(nominees, holm, strict=True) if ok and (rows[n]["mean_net_pad2"] or 0) > 0]
    return {**header("heldout", sessions), "variants": rows, "nominated": nominees, "passed": passed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inputs", "discovery", "heldout"))
    mode = parser.parse_args().mode
    if mode == "inputs":
        return inputs_check()
    result = discovery() if mode == "discovery" else held_out()
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{mode}.json"
    path.write_text(json.dumps(result, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"{path.relative_to(ROOT)}: nominated {result['nominated']}" + (
        f", passed {result['passed']}" if mode == "heldout" else ""))  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
