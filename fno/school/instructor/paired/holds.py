"""A driver card's frozen hold in sessions (story MS-INS, part d): the batch length of its comparisons, so batches are
roughly independent (a position held h sessions links h neighbouring sessions). The shortest bound the card states:
sessions held, calendar days held, sessions before expiry, or days to expiry at entry less its last exit day; with
none, the longest cycle of its roads' expiries. Days become sessions at 5 a week, rounded up. N0 holds nothing."""

import math

from ...constants import ExpiryKind
from ...contracts.decisions import DriverCard
from ...contracts.roads import ROADS_BY_CODE
from ...drivers.exits import LAST_SESSION_DTE, MAX_DAYS, MAX_SESSIONS
from ..thresholds import BATCH_HOLD_MULTIPLE, MIN_BATCH, MONTHLY_CYCLE_DAYS, SESSIONS_PER_WEEK, WEEKLY_CYCLE_DAYS

NOTHING_FAMILY = "nothing"  # N0's card family
DTE_MAX, SESSIONS_BEFORE_MAX = "dte_max", "sessions_before_max"  # e's entry parameters that bound a hold
CYCLE_DAYS = {ExpiryKind.MONTHLY: MONTHLY_CYCLE_DAYS, ExpiryKind.WEEKLY: WEEKLY_CYCLE_DAYS}


def sessions_in(days: float) -> int:
    return math.ceil(days * SESSIONS_PER_WEEK / 7)


def hold_sessions(card: DriverCard) -> int:
    if card.family == NOTHING_FAMILY:
        return 0
    p = card.parameters
    cycle = p.get(DTE_MAX) or max(CYCLE_DAYS[ROADS_BY_CODE[r].expiry_kind] for r in card.roads)
    bounds = [sessions_in(float(cycle) - float(p.get(LAST_SESSION_DTE) or 0))]
    if p.get(MAX_SESSIONS):
        bounds.append(int(p[MAX_SESSIONS]))
    if p.get(MAX_DAYS):
        bounds.append(sessions_in(float(p[MAX_DAYS])))
    if p.get(SESSIONS_BEFORE_MAX):
        bounds.append(int(p[SESSIONS_BEFORE_MAX]))
    return max(min(bounds), 1)


def pair_batch(driver: DriverCard, control: DriverCard) -> int:
    """The batch length of a pair: 1.5 x the longer hold, rounded up, never under `MIN_BATCH` (the null gate's rule)."""
    return max(math.ceil(BATCH_HOLD_MULTIPLE * max(hold_sessions(driver), hold_sessions(control))), MIN_BATCH)
