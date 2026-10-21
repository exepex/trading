"""Print the v4 freeze record's two file lists (the freeze plan, response 287): the byte-checked table with each
file's SHA-256, then the files recorded but not checked. The freeze commit pastes them into
`research/forecasts/FREEZE_v4.md`; `fno.forecast_scoring.v4.freeze_check.problems` then checks the repository against
them.

    python tools/v4_freeze_table.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fno.forecast_scoring.v4.freeze_check import recorded, table  # noqa: E402


def main() -> None:
    print("## Frozen files (checked byte for byte)\n")
    print(table(ROOT))
    print("\n## Recorded, not byte-checked\n")
    print(recorded())


if __name__ == "__main__":
    main()
