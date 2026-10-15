"""The entry check (story E4c, decisions 30 and 43): before any leg fills, at the execution snapshot, every leg's
opening side must fill and every protective (bought) leg must also be sellable back there. On paper every quote of the
snapshot is known before the first fill, so a trade that would be unwound, or closed at once because its protection
cannot be sold, is refused before anything is bought (design 3.2: all legs fill at one snapshot or none).

It prices with E4's `price_leg`, so it adds no second pricing rule, and depends only on the snapshot it is given, so
E8 can apply it at each of its snapshots. A problem names the contract and the units, never a quote figure (E2b)."""

from __future__ import annotations

from collections.abc import Sequence

from ..constants import PROTECTION_NOT_BUYABLE, PROTECTION_NOT_SELLABLE, SHORT_LEG_NOT_SELLABLE
from .pricing import DeskLeg, price_leg
from .snapshot import ExecutionSnapshot

PROBLEM = "{code} ({contract}, {units} units)"


def entry_problems(snapshot: ExecutionSnapshot, legs: Sequence[DeskLeg], units: int) -> list[str]:
    """Every failing check, in the fixed order: the legs as given (E4's order, protection first), for each its opening
    side, then a protective leg's closing side. Empty when the entry may fill."""
    problems = []
    for leg in legs:
        if not price_leg(snapshot, leg, leg.side(opening=True), units).fills:
            code = PROTECTION_NOT_BUYABLE if leg.protective else SHORT_LEG_NOT_SELLABLE
        elif leg.protective and not price_leg(snapshot, leg, leg.side(opening=False), units).fills:
            code = PROTECTION_NOT_SELLABLE
        else:
            continue
        problems.append(PROBLEM.format(code=code, contract=leg.contract, units=units))
    return problems
