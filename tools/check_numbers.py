"""Check the numbered series against their registries in `numbers/` (story O12); standard library only.

    python tools/check_numbers.py          # one line per problem, exit 1 when any; CI runs it on every push
    python tools/check_numbers.py --seed   # when O12 merges: register the files on main as `existing` history and
                                           # pin it in fno/numbering/seed_pins.json (a later run is a judged change)

Fails when a numbered file (or a numbered `## Addendum` heading) has no registry row, when a number is used twice
outside the seeded history, when the seeded history differs from its pin, when a series file is misnamed, or when a
row is malformed. A row with no file yet is a claim still being written.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fno.numbering.check import check_numbers  # noqa: E402
from fno.numbering.seed import seed_registries  # noqa: E402

CLEAN = "number check: clean"
FAILED = "number check: FAILED, {count} problem(s); claim numbers with tools/claim_number.py (docs/stories/O12)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT, help="the checkout to check (default: this one)")
    parser.add_argument("--seed", action="store_true", help="register the files already present, as history")
    args = parser.parse_args(argv)
    if args.seed:
        print(f"number seed: {seed_registries(args.root)} row(s) added")
    problems = check_numbers(args.root)
    for line in problems:
        print(line)
    print(FAILED.format(count=len(problems)) if problems else CLEAN)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
