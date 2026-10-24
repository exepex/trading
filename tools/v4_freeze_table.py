"""Print the v4 freeze record's generated sections (the freeze plan, response 287; story G6 freeze, criterion 9): the
byte-checked table with each file's SHA-256, the files recorded but not checked, the platform the freeze ran on, and
the disclosure of every back-fill, live row and report made on or before the freeze day. The freeze commit pastes them
into `research/forecasts/FREEZE_v4.md`; `fno.forecast_scoring.v4.freeze_check.freeze_problems` then checks the
repository against them.

    python tools/v4_freeze_table.py --frozen-on 2026-10-25
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fno.forecast_scoring.v4.freeze_check import recorded, table  # noqa: E402
from fno.forecast_scoring.v4.freeze_disclosure import disclosure  # noqa: E402


def platform_line() -> str:
    """The judge 508 libm limit: a last-bit difference between C libraries can move a replayed value."""
    import numpy

    libc = "-".join(platform.libc_ver()) or "unknown"
    return f"Python {platform.python_version()}, numpy {numpy.__version__}, C library {libc}, {platform.machine()}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--frozen-on", type=date.fromisoformat, required=True, help="the record's Frozen on day")
    frozen_on = parser.parse_args().frozen_on
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
    print("## Frozen files (checked byte for byte)\n")
    print(table(ROOT))
    print("\n## Recorded, not byte-checked\n")
    print(recorded())
    print(f"\n## Platform\n\n{platform_line()}")
    print(f"\n## Disclosure (protocol section 8), as of commit `{head.stdout.strip()}`\n")
    print(disclosure(ROOT, frozen_on))


if __name__ == "__main__":
    main()
