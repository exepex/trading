"""Protocol section 8's lot cross-check (revision 5), from the cached F&O rows (`edge1study/panels.py`): per index,
every legacy-file derived lot more than 5% from the circular schedule (`edge1study/lots.py`), then each expiry's
board lot in the UDiFF files when first listed and every change during its life; LOT_CHECK.md compares each change
with NSE's circular.

    python research/edge1/lot_changes.py   # needs the cache
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from edge1study.inputs import sessions  # noqa: E402
from edge1study.lots import UDIFF, disagreements  # noqa: E402
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
        found = disagreements(index, rows[index])
        print(f"## {index}: {len(found)} legacy-file lots more than 5% from the circular schedule")
        for day, expiry, derived, circular in found:
            print(f"  {day} expiry {expiry}: derived {derived}, circular {circular}")
        print(f"## {index}: NSE's board lot (UDiFF files), each expiry's first lot and every change")
        previous = None
        for expiry, life in sorted(lot_lives([r for r in rows[index] if r.source == UDIFF]).items()):
            first = life[0][1]
            if first != previous or len(life) > 1:
                changes = ", ".join(f"{d} {lot}" for d, lot in life)
                print(f"{expiry}: {changes}")
            previous = life[-1][1]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
