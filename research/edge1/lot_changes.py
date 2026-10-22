"""Protocol section 8's lot cross-check, its input: every change in each index's lot series, from the cached F&O rows
(`edge1study/panels.py`). Prints, per index, each monthly expiry's lot when first listed and every change during its
life; LOT_CHECK.md compares each change with NSE's circular.

    python research/edge1/lot_changes.py   # needs the cache
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from edge1study.inputs import sessions  # noqa: E402
from edge1study.panels import cached_rows  # noqa: E402
from edge1study.runner import BANKNIFTY, INDICES  # noqa: E402

from fno.storage.wiring import build_nifty_panel_files, build_session_calendar  # noqa: E402


def lot_lives(rows) -> dict:
    """expiry -> [(day, lot)] at each day the lot differs from the day before (the first day included)."""
    lives: dict = {}
    for row in sorted(rows, key=lambda r: r.day):
        for expiry, lot in row.lots.items():
            life = lives.setdefault(expiry, [])
            if not life or life[-1][1] != lot:
                life.append((row.day, lot))
    return lives


def main() -> int:
    fo_files, _ = build_nifty_panel_files()
    rows = cached_rows(INDICES, sessions(build_session_calendar()), fo_files, options_for=(BANKNIFTY,))
    for index in INDICES:
        print(f"## {index}")
        previous = None
        for expiry, life in sorted(lot_lives(rows[index]).items()):
            first = life[0][1]
            if first != previous or len(life) > 1:
                changes = ", ".join(f"{d} {lot}" for d, lot in life)
                print(f"{expiry}: {changes}")
            previous = life[-1][1]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
