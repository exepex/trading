"""R2 feasibility study (PROTOCOL.md, AMENDMENT_1.md, AMENDMENT_2.md): stock options around company results.

    python study.py --check  [--cache DIR]                 file counts and schemas only (no stage numbers)
    python study.py --fetch  [--cache DIR]                 copy the raw files to the cache, hashes checked
    python study.py --fill-results-dates                   A12's board-meeting day lists into Drive (A12's classes)
    python study.py --run [--cache DIR] [--snapshot PATH SHA256]  the one run: writes results.json and results.md
        (PATH: the raw snapshot's Drive path under raw/, SHA256: the hash snapshot.py printed)

Research only: read-only on market data, no order code. Runs once (PROTOCOL.md section 11).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1])]

from r2study.analysis import run  # noqa: E402
from r2study.report import results_json, results_markdown  # noqa: E402
from r2study.wiring import (  # noqa: E402
    INDEX_CLOSE,
    LEGACY,
    UDIFF,
    build_inputs,
    check_frozen,
    fill_results_dates,
    sessions_from_manifests,
    trials_total,
)

OUTPUTS = ("results.json", "results.md")

DEFAULT_CACHE = Path.home() / ".cache" / "r2-study"  # outside the checkout: raw copies never near the repository


def check(cache_folder: Path) -> None:
    """File counts per dataset and the column names of one file of each format: no values."""
    from r2study.inputs import InputCache

    from fno.fo_bhavcopy import csv_text

    cache = InputCache(cache_folder, lambda path: None)
    sessions = sessions_from_manifests()
    print(f"sessions {sessions.days[0]} to {sessions.last}: {len(sessions.days)}")
    for dataset in (UDIFF, LEGACY, INDEX_CLOSE):
        days = cache.days(dataset)
        cached = [d for d in days if cache.read(dataset, d) is not None]
        print(f"{dataset.name}: manifest {len(days)}, cached {len(cached)}")
        if cached and dataset is not INDEX_CLOSE:
            name, data = cache.read(dataset, cached[-1])
            print(f"  columns: {csv_text(name, data).splitlines()[0]}")


def fetch(cache_folder: Path) -> None:
    from r2study.inputs import InputCache

    from fno.storage.wiring import build_drive_reader

    cache = InputCache(cache_folder, build_drive_reader().get)
    for dataset in (INDEX_CLOSE, UDIFF, LEGACY):
        cache.fetch(dataset)


def uncached(cache_folder: Path) -> list[str]:
    """Manifest days of the F&O and index-close datasets with no checked local copy."""
    from r2study.inputs import InputCache, cached_file

    cache = InputCache(cache_folder, lambda path: None)
    return [f"{d.name} {day}" for d in (UDIFF, LEGACY, INDEX_CLOSE) for day in cache.days(d)
            if not cached_file(cache_folder, d, day).exists()]  # fmt: skip


def run_once(cache_folder: Path, snapshot: list[str] | None, workers: int) -> None:
    check_frozen()
    missing = uncached(cache_folder)
    if missing:
        raise RuntimeError(f"{len(missing)} raw files not cached (run --fetch first): {missing[:3]}")
    sessions = sessions_from_manifests()
    inputs = build_inputs(cache_folder, tuple(snapshot) if snapshot else None, workers, sessions.last)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    out = results_json(run(inputs), trials_total(), commit)
    (HERE / "results.json").write_text(json.dumps(out, indent=1) + "\n")
    (HERE / "results.md").write_text(results_markdown(out))
    print(f"{out['answer']['answer']} ({out['answer']['stage']}); {out['trial']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--fetch", action="store_true")
    mode.add_argument("--fill-results-dates", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument(
        "--snapshot", nargs=2, metavar=("PATH", "SHA256"), help="the raw snapshot in Drive and its hash"
    )
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args(argv)
    if args.check:
        check(args.cache)
    elif args.fetch:
        fetch(args.cache)
    elif args.fill_results_dates:
        return 0 if fill_results_dates(sessions_from_manifests().last).complete else 1
    else:
        if any((HERE / name).exists() for name in OUTPUTS):
            print("results exist: the study runs once (PROTOCOL.md section 11)")
            return 1
        run_once(args.cache, args.snapshot, args.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
