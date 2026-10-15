"""Study FT1, the fill-timing study (story E8a; PROTOCOL.md).

    python study.py --probe     the coverage probe: symbols and candle counts only, no price (before the freeze)

Research only: read-only on market data, no order code.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1])]

from ft1study.probe import FIELDS, probe  # noqa: E402
from ft1study.wiring import (  # noqa: E402
    build_calendar,
    build_contract_candles,
    build_contracts,
    sessions_before,
    window_expiries,
)

PROBE_FILE = HERE / "probe.csv"


def run_probe() -> None:
    contracts = build_contracts()
    rows = probe(contracts, window_expiries(contracts), build_contract_candles(), sessions_before(build_calendar()))
    with PROBE_FILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(FIELDS)
        writer.writerows(row.as_row() for row in rows)
    print(f"probe: {sum(r.answered for r in rows)} of {len(rows)} answered; written {PROBE_FILE.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    if args.probe:
        run_probe()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
