"""EDGE2 F9 (protocol `research/edge2/F9_PROTOCOL.md`): the implied-volatility crush around scheduled RBI, Budget and
election days on NIFTY and BANKNIFTY monthly options, against ordinary days. Exploratory: it can nominate, never
prove. The held-out read (FINNIFTY, MIDCPNIFTY) is not built: it waits for a nomination, a judge and LOT_CHECK.md.

    python research/edge2/study_f9.py inputs      # counts only: events, setups and skips, no trade priced
    python research/edge2/study_f9.py discovery   # writes research/edge2/f9/discovery.json (commit it)
"""

from __future__ import annotations

import argparse
import csv
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

from f9study import summary  # noqa: E402
from f9study.files import cached_rows  # noqa: E402
from f9study.trades import EXITS, STRUCTURES, priced, setup  # noqa: E402

OUT, EVENTS = HERE / "f9", HERE / "f9_events.csv"
FIRST_DAY, LAST_DAY = date(2019, 1, 1), date(2026, 10, 23)
SYMBOLS, CONTROL_GAP = ("NIFTY", "BANKNIFTY"), 2  # a control day has no event within 2 sessions
TRIALS = dict(zip([f"EDGE2-F9-{c}-{e}" for c in STRUCTURES for e in EXITS], range(124, 128)))
PADS = (1.0, 2.0)


def code_hash() -> str:
    files = sorted((HERE / "f9study").glob("*.py")) + [Path(__file__), EVENTS]
    return hashlib.sha256(b"".join(f.read_bytes() for f in files)).hexdigest()


def sessions() -> list[date]:
    from fno.storage.wiring import build_session_calendar

    cal = build_session_calendar()
    return [d for d in cal.sessions(FIRST_DAY, LAST_DAY) if cal.session_kind(d) in ("regular", "special")]


def events(days: list[date]) -> dict[date, str]:
    """Scheduled events whose date was announced before their entry session (the session before the event)."""
    found = {}
    with EVENTS.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            day = date.fromisoformat(row["date"])
            before = [d for d in days if d < day]
            if before and date.fromisoformat(row["announced_on"]) < before[-1]:
                found[day] = row["type"]
    return found


def control_days(days: list[date], event_days: dict[date, str]) -> list[date]:
    index = {d: i for i, d in enumerate(days)}
    near = set()
    for e in event_days:
        i = next((j for j, d in enumerate(days) if d >= e), None)
        if i is not None:
            near.update(days[max(0, i - CONTROL_GAP) : i + CONTROL_GAP + 1])
    return [d for d in days if d not in near and 0 < index[d] < len(days) - 2]


def setups(days, rows, event_days, exit_code):
    return [setup(s, e, exit_code, days, rows[s]) for e in event_days for s in SYMBOLS]


def runs(days, rows, event_days, controls, charges) -> dict:
    kinds = {**event_days, **dict.fromkeys(controls, "control")}
    found = {}
    for name in TRIALS:
        code, exit_code = name.split("-")[2:]
        on_events, on_controls = setups(days, rows, event_days, exit_code), setups(days, rows, controls, exit_code)
        found[name] = {"pad1": priced(code, on_events, rows, charges, PADS[0], kinds),
                       "pad2": priced(code, on_events, rows, charges, PADS[1], kinds),
                       "control": priced(code, on_controls, rows, charges, PADS[0], kinds)}  # fmt: skip
    return found


def header(mode: str) -> dict:
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return {"mode": mode, "exploratory": True, "protocol": "research/edge2/F9_PROTOCOL.md", "head": head,
            "code_sha256": code_hash(), "trials": TRIALS}  # fmt: skip


def inputs_check() -> int:
    days = sessions()
    rows, event_days = cached_rows(SYMBOLS, days), events(days)
    built = setups(days, rows, event_days, "E0")
    controls = control_days(days, event_days)
    print(json.dumps({**header("inputs"), "sessions": len(days), "events": len(event_days),
                      "by_type": dict(Counter(event_days.values())), "control_days": len(controls),
                      "setups": dict(Counter(s.status for s in built))}))  # fmt: skip
    return 0


def discovery() -> dict:
    from fno.config import load_app_config

    days = sessions()
    rows, event_days = cached_rows(SYMBOLS, days), events(days)
    found = runs(days, rows, event_days, control_days(days, event_days), load_app_config()["charges"])
    variants = summary.family(found)
    gamma = {name: summary.gamma_report(r["pad1"]) for name, r in found.items()}
    return {**header("discovery"), "events": len(event_days), "variants": variants, "gamma": gamma,
            "nominated": summary.nominated(variants)}  # fmt: skip


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inputs", "discovery"))
    mode = parser.parse_args().mode
    if mode == "inputs":
        return inputs_check()
    result = discovery()
    OUT.mkdir(exist_ok=True)
    path = OUT / "discovery.json"
    path.write_text(json.dumps(result, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"{path.relative_to(ROOT)}: nominated {result['nominated']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
