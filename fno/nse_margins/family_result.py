"""One structure family's share of a stress-factor run (story A14c families; owner, 16 Oct 2026): the holdings it
counts, its largest needed factor (carried forward on an incremental run), the guardrails' decision against the
family's factor in force, and the peak that sets it. Debit and credit never mix."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..constants import STRUCTURE_FAMILIES
from .held_rise import Holding
from .stress_log import LastRow, StressRowRefused, decide

FELL_APPROVED = "; fall approved by the owner, DESK_DECISIONS {approved}"


@dataclass(frozen=True)
class FamilyResult:
    family: str
    last: LastRow
    counted: list[Holding]
    unrounded: float
    factor: float
    computed: float
    status: str
    peak: str


def family_result(family: str, completed: list[Holding], last: LastRow, full: bool,
                  approved_fall: str | None) -> FamilyResult:  # fmt: skip
    counted = [h for h in completed if STRUCTURE_FAMILIES[h.structure] == family
               and (full or h.exit > last.coverage_through)]  # fmt: skip
    carried = None if full else last.unrounded
    if not counted and carried is None:
        raise StressRowRefused(f"no {family} holding completed in the archive")
    new_max = max((h.needed for h in counted), default=0.0)
    unrounded = max(new_max, carried or 0.0)
    factor, computed, status = decide(last, unrounded, approved_fall)
    fell = approved_fall if factor < last.factor else None  # the approval is named only on a real fall
    peak = _peak(counted, new_max, carried, last.coverage_through) + (
        FELL_APPROVED.format(approved=fell) if fell else ""
    )
    return FamilyResult(family, last, counted, unrounded, factor, computed, status, peak)


def _peak(counted: list[Holding], new_max: float, carried: float | None, through: date | None) -> str:
    if carried is not None and carried >= new_max:
        return f"carried from the run through {through}"
    h = max(counted, key=lambda h: (h.needed, -h.entry.toordinal()))
    return f"{h.structure} {h.width:g} entered {h.entry} peak {h.peak_day} needed {h.needed:.4f}"
