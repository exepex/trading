"""Study FT1, the fill-timing study (story E8a; PROTOCOL.md).

    python study.py --probe     the coverage probe: symbols and candle counts only, no price (before the freeze)
    python study.py --dry-run   the fetch for 5 decision days: call count and duration (archived, reused by --fetch)
    python study.py --fetch     every planned contract window, raw answers to Drive with a manifest row each
    python study.py --run       once, from the archived answers only: results.json and results.md

Research only: read-only on market data, no order code.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1])]

from ft1study import wiring  # noqa: E402
from ft1study.freeze import check_frozen  # noqa: E402
from ft1study.plan import fetch_plan  # noqa: E402
from ft1study.probe import FIELDS, probe  # noqa: E402
from ft1study.report import render  # noqa: E402
from ft1study.steps import TRIAL, dry_run_items, prepare, results  # noqa: E402

PROBE_FILE = HERE / "probe.csv"


def run_probe() -> None:
    contracts = wiring.build_contracts()
    calendar = wiring.build_calendar()
    rows = probe(contracts, wiring.window_expiries(contracts), wiring.build_contract_candles(),
                 wiring.sessions_before(calendar))  # fmt: skip
    with PROBE_FILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(FIELDS)
        writer.writerows(row.as_row() for row in rows)
    print(f"probe: {sum(r.answered for r in rows)} of {len(rows)} answered; written {PROBE_FILE.name}")


def _prepared():
    contracts, index = wiring.build_contracts(), wiring.build_index_levels()
    prepared = prepare(wiring.build_calendar(), contracts, wiring.build_structures(), index, wiring.WINDOW_FIRST,
                       wiring.WINDOW_LAST)  # fmt: skip
    return contracts, index, prepared


def run_fetch(dry_run: bool) -> None:
    from fno.research_engine.ledger import Ledger

    Ledger(HERE.parents[1]).require_registered(TRIAL)  # registered and frozen before any price is fetched
    *_, prepared = _prepared()
    plan = fetch_plan(prepared.entries)
    items = dry_run_items(prepared) if dry_run else plan
    report = wiring.build_fetcher(archive := wiring.build_archive()).run(items)
    print(f"{'dry run' if dry_run else 'fetch'}: {report.line()}; full plan {len(plan)} windows")
    for item in report.failed:
        print(f"failed: {item.symbol} {item.start}..{item.end}")
    print(f"manifest rows: {len(archive.rows())}")


def run_study() -> None:
    check_frozen(TRIAL)
    contracts, index, prepared = _prepared()
    terms = wiring.build_terms()
    observer = wiring.build_observer(wiring.build_archive(), contracts, index, terms)
    families = [s.code for s in wiring.build_structures()]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    window = f"{wiring.WINDOW_FIRST} to {wiring.WINDOW_LAST}"
    found = results(prepared, observer, families, terms.lot, wiring.read_a4_snapshots(), window, commit)
    (HERE / "results.json").write_text(json.dumps(found, indent=1, default=str) + "\n", encoding="utf-8")
    (HERE / "results.md").write_text(render(found), encoding="utf-8")
    print("written results.json and results.md")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    for flag in ("--probe", "--dry-run", "--fetch", "--run"):
        group.add_argument(flag, action="store_true")
    args = parser.parse_args()
    if args.probe:
        run_probe()
    elif args.dry_run or args.fetch:
        run_fetch(dry_run=args.dry_run)
    elif args.run:
        run_study()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
