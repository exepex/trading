"""From events to what each one's analysis reads (PROTOCOL.md sections 3-5, amendment 1 sections D3-D6).

Exit-session data is read for contracts traded and listed strikes only, never for prices.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date

from .bhav import Chain, DaySummary
from .evaluate import EventMarket
from .events import Event
from .lots import LotSizes
from .sessions import Sessions, choose_expiry
from .sources import CorporateActions
from .structures import Strikes, atm_strikes

LOT_UNKNOWN, CORPORATE_ACTION, NO_ATM, NO_EXPIRY, NO_FUTURE = (
    "lot unknown",
    "corporate action",
    "no listed ATM strike",
    "no expiry at least 5 sessions after R",
    "no stock future close on entry",
)


@dataclass(frozen=True)
class Plan:
    """An event that passed the exclusions, with its expiry and strikes chosen on the entry session."""

    event: Event
    lot: int
    underlying: float
    expiry: date
    pushed: bool
    strikes: Strikes
    entry: Chain


def screen_lots(events: list[Event], lots: LotSizes, actions: CorporateActions) -> tuple[list, Counter]:
    """(event, lot) for events whose lot is known and unchanged to R and with no listed action in (entry, R]."""
    kept, counts = [], Counter()
    for event in events:
        lot = lots.lot(event.symbol, event.entry)
        if lot is None:
            counts[LOT_UNKNOWN] += 1
            continue
        listed = actions.covers(event.entry, event.reaction) and actions.between(
            event.symbol, event.entry, event.reaction
        )
        if listed or lots.lot(event.symbol, event.reaction) != lot:
            counts[CORPORATE_ACTION] += 1
            continue
        kept.append((event, lot))
    return kept, counts


def plan_event(
    event: Event, lot: int, summary: DaySummary, chains: dict[date, Chain], sessions: Sessions
) -> tuple[Plan | None, str]:
    """Expiry and strikes on the entry session (`chains`: the stock's option chains that day, by expiry)."""
    future = summary.near_future(event.symbol)
    if future is None or future.close <= 0:
        return None, NO_FUTURE
    expiry, pushed = choose_expiry(sessions, list(chains), event.reaction)
    if expiry is None:
        return None, NO_EXPIRY
    strikes = atm_strikes(chains[expiry], future.close)
    if strikes is None:
        return None, NO_ATM
    return Plan(event, lot, future.close, expiry, pushed, strikes, chains[expiry]), ""


def needed_days(plans: list[Plan], sessions: Sessions) -> dict[date, set[str]]:
    """Sessions (R and the one before entry) whose option rows the plans need, with the stocks needed."""
    days: dict[date, set[str]] = defaultdict(set)
    for plan in plans:
        days[plan.event.reaction].add(plan.event.symbol)
        previous = sessions.before(plan.event.entry)
        if previous is not None:
            days[previous].add(plan.event.symbol)
    return days


def market(
    plan: Plan, sector: str | None, exit_chain: Chain | None, previous_chain: Chain | None
) -> EventMarket | None:
    """The event's market, or None when K0 is no longer listed on R (an F&O adjustment: corporate action)."""
    exit_chain = exit_chain or {}
    if not any(strike == plan.strikes.k0 for strike, _ in exit_chain):
        return None
    return EventMarket(
        symbol=plan.event.symbol,
        reaction=plan.event.reaction,
        sector=sector,
        lot=plan.lot,
        strikes=plan.strikes,
        entry=plan.entry,
        exit=exit_chain,
        previous=previous_chain or {},
    )
