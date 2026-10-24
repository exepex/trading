"""Each cycle's market lot (protocol section 8, revision 5).

- From 2024 (UDiFF files): NSE's own `NewBrdLotQty`, as each day's file states it.
- Before (legacy files, no lot column): NSE's circular schedule below. The derived lot (`day_files.derived_lot`) is
  only its check: turnover is traded at the day's average price, not the settlement price, so the derived figure
  wanders (72-77 around NIFTY's 75 in 2019-21, 49-51 around 50) and is never used as the lot. A derived lot more
  than TOLERANCE from the schedule is listed as a disagreement (`disagreements`, printed by `lot_changes.py`).

Each change applies from the first monthly expiry the circular names; earlier expiries keep the old lot to expiry."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from .day_files import DayRows

UDIFF = "udiff"
TOLERANCE = 0.05
# index -> (lot before the first change, ((first expiry month, lot, source), ...)), as found in the build (22 Oct)
SCHEDULE = {
    "NIFTY": (75, ((date(2021, 7, 1), 50, "NSE/FAOP/47854, 31 Mar 2021: 75 to 50 from the July 2021 expiry"),)),
    "BANKNIFTY": (20, ((date(2020, 7, 1), 25, "NSE revision of June 2020 (Zerodha bulletin, 26 Jun 2020; circular "
                                              "number not found): 20 to 25 from the July 2020 monthly"),
                       (date(2023, 7, 1), 15, "NSE/FAOP/56233, 31 Mar 2023: 25 to 15 from the July 2023 expiry"))),
}  # fmt: skip


def circular_lot(index: str, expiry: date) -> int:
    lot, changes = SCHEDULE[index]
    for first_expiry, changed, _ in changes:
        if expiry >= first_expiry:
            lot = changed
    return lot


def market_lots(index: str, rows: Iterable[DayRows]) -> dict[date, dict[date, int]]:
    """day -> expiry -> units per lot: UDiFF's board lot, else the circular schedule for each expiry of the day."""
    return {r.day: dict(r.lots) if r.source == UDIFF else {e: circular_lot(index, e) for e in r.lots} for r in rows}


def disagreements(index: str, rows: Iterable[DayRows]) -> list[tuple[date, date, int, int]]:
    """(day, expiry, derived, circular) for each legacy-file lot more than TOLERANCE from the schedule."""
    legacy = [(r.day, e, lot) for r in rows if r.source != UDIFF for e, lot in sorted(r.lots.items())]
    return [
        (d, e, lot, circular_lot(index, e)) for d, e, lot in legacy if abs(lot / circular_lot(index, e) - 1) > TOLERANCE
    ]
