"""What one NSE index-list answer says (pure): its stamp, and each index's `last` and `open`. A list counts only when
its stamp is today at or after 15:30; any other answer is refused with a reason that holds no level."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from .constants import INDICES, STAMP_FORMAT, STAMP_FROM


class Refused(Exception):
    """The answer is not today's close; the message names why (never a level)."""


@dataclass(frozen=True)
class ListRead:
    stamp: str  # NSE's text, e.g. "21-Oct-2026 15:30"
    values: dict[str, dict[str, float]]  # listed name -> {"last": .., "open": ..}


def read_answer(payload: dict, day: date) -> ListRead:
    stamp = str(payload.get("timestamp") or "").strip()
    if not stamp:
        raise Refused("NSE answer has no timestamp")
    try:
        stamped = datetime.strptime(stamp, STAMP_FORMAT)
    except ValueError as error:
        raise Refused(f"NSE stamp {stamp!r} is not readable") from error
    if stamped.date() != day:
        raise Refused(f"NSE stamp {stamp} is not today's session")
    if stamped.time() < STAMP_FROM:
        raise Refused(f"NSE stamp {stamp} is before {STAMP_FROM:%H:%M}")
    rows = {str(row.get("index", "")).strip(): row for row in payload.get("data") or ()}
    return ListRead(stamp, {name.listed: _values(rows, name.listed) for name in INDICES})


def _values(rows: dict, name: str) -> dict[str, float]:
    row = rows.get(name)
    if row is None:
        raise Refused(f"{name} missing from the answer")
    try:
        return {"last": float(row["last"]), "open": float(row["open"])}
    except (KeyError, TypeError, ValueError) as error:
        raise Refused(f"{name} has no readable last or open") from error


def difference(first: float, second: float) -> str:
    """`same`, or `differs by X` (a derived difference, never a level)."""
    gap = abs(first - second)
    return "same" if gap < 0.005 else f"differs by {gap:.2f}"
