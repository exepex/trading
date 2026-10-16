"""BR1a's studies (docs/stories/BR-breadth.md). Research only, read-only inputs.

    python -I research/breadth/studies/run.py panel <legacy zips> <udiff zips> <scratch>   # the three panel tables
    python -I research/breadth/studies/run.py studies <scratch> research/breadth/studies/results

The zip folders are copies of the Drive raw archive (`research/2026-10-15-breadth-sizing/fetch.py`, both formats).
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[2])]

from brstudy import panel, runner, verify  # noqa: E402

PANEL, LEGACY_OVERLAP, UDIFF_OVERLAP = "panel.csv", "overlap_legacy.csv", "overlap_udiff.csv"


def main(command: str, *args: str) -> None:
    if command == "panel":
        legacy_zips, udiff_zips, scratch = map(Path, args)
        checked = verify.verify(legacy_zips, "legacy"), verify.verify(udiff_zips, "udiff")
        print(f"verified {checked[0]} legacy and {checked[1]} udiff files against the manifests")
        panel.build(legacy_zips, udiff_zips, scratch / PANEL)
        panel.overlap(legacy_zips, udiff_zips, scratch / LEGACY_OVERLAP, scratch / UDIFF_OVERLAP)
    elif command == "studies":
        scratch, out = map(Path, args)
        runner.run(scratch / PANEL, scratch / LEGACY_OVERLAP, scratch / UDIFF_OVERLAP, out)
    else:
        raise SystemExit(f"unknown command {command!r}: panel | studies")


if __name__ == "__main__":
    main(*sys.argv[1:])
