"""Story E8a criterion 2: two days a judge recomputes by hand from the archived raw answers. For one 15:00 and one
14:00 decision day (fixed positions in the decision-day list, chosen before the run) and the families SF and LC: the
strikes and symbols, the leg prices at the decision and at each fill, `C`, and whether the entry flipped. Only the flip
label leaves the P&L, as the report's flip shares do."""

from __future__ import annotations

from collections.abc import Sequence

from .contracts import option_symbol
from .entries import Entry, main_width
from .observe import Observer
from .times import DECISION_14, DECISION_15, REACTIONS, fill_moment

HAND_DAYS = {DECISION_15: 99, DECISION_14: 299}  # positions in the decision-day list
HAND_FAMILIES = ("SF", "LC")


def flip_label(at_decision: float | None, at_fill: float | None) -> str:
    if at_decision is None:
        return "not settled"
    if at_decision > 0 and not at_fill > 0:
        return "bad flip"
    return "good flip" if at_decision <= 0 < at_fill else "no flip"


def hand_check(days: Sequence, entries: Sequence[Entry], observer: Observer) -> list[dict]:
    chosen = {(days[i].day, at) for at, i in HAND_DAYS.items() if i < len(days)}
    picked = [e for e in entries if (e.day.day, e.decision.at) in chosen and e.family in HAND_FAMILIES
              and e.width == main_width(e.family)]  # fmt: skip
    return [_entry(e, observer) for e in picked]


def _entry(entry: Entry, observer: Observer) -> dict:
    decided, why = observer.leg_prices(entry, entry.decision)
    out = {"day": entry.day.day, "decision": f"{entry.decision.at:%H:%M}", "family": entry.family,
           "expiry": entry.day.expiry, "spot": entry.spot, "excluded_at_decision": why,
           "legs": [[option_symbol(entry.day.expiry, leg.strike, leg.kind), leg.side] for leg in entry.legs or ()],
           "decision_prices": decided, "fills": {}}  # fmt: skip
    for reaction in REACTIONS:
        fill = fill_moment(entry.decision, reaction, observer.market.next_session)
        seen = observer.observe(entry, reaction)
        out["fills"][reaction] = {"at": f"{fill.day} {fill.at:%H:%M}", "prices": observer.leg_prices(entry, fill)[0],
                                  "c": seen.c, "excluded": seen.excluded,
                                  "flip": flip_label(seen.pnl_decision, seen.pnl_fill)}  # fmt: skip
    return out
