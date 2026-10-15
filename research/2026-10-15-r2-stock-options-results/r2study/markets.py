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
from .lots import LegacyLots, chain_lot
from .sessions import Sessions, choose_expiry
from .sources import CorporateActions
from .structures import Strikes, atm_strikes

LOT_UNKNOWN, LOT_UNKNOWN_ON_R, CORPORATE_ACTION, NO_ATM, NO_EXPIRY, NO_FUTURE = (
    "lot unknown",
    "lot unknown on R",
    "corporate action",
    "no listed ATM strike",
    "no expiry at least 5 sessions after R",
    "no stock future close on entry",
)


@dataclass(frozen=True)
class Plan:
    """An event that passed the exclusions, with its expiry, strikes and lot chosen on the entry session."""

    event: Event
    lot: int
    lot_from_column: bool  # the current format's lot column (checked again on R), else the legacy derivation
    underlying: float
    expiry: date
    pushed: bool
    strikes: Strikes
    entry: Chain


def screen_actions(events: list[Event], actions: CorporateActions) -> tuple[list[Event], Counter]:
    """Events with no listed F&O-changing action in (entry, R], where NSE's list covers the dates."""
    kept, counts = [], Counter()
    for event in events:
        if actions.covers(event.entry, event.reaction) and actions.between(event.symbol, event.entry, event.reaction):
            counts[CORPORATE_ACTION] += 1
        else:
            kept.append(event)
    return kept, counts


def plan_event(
    event: Event, summary: DaySummary, chains: dict[date, Chain], sessions: Sessions, legacy: LegacyLots | None
) -> tuple[Plan | None, str]:
    """Expiry, strikes and lot on the entry session (`chains`: the stock's option chains that day, by expiry;
    `legacy`: the validated legacy rule, or None when it failed validation)."""
    future = summary.near_future(event.symbol)
    if future is None or future.close <= 0:
        return None, NO_FUTURE
    expiry, pushed = choose_expiry(sessions, list(chains), event.reaction)
    if expiry is None:
        return None, NO_EXPIRY
    strikes = atm_strikes(chains[expiry], future.close)
    if strikes is None:
        return None, NO_ATM
    lot = chain_lot(chains[expiry], strikes.k0)
    from_column = lot is not None
    if lot is None and legacy is not None:
        lot = legacy.derived(event.symbol, event.entry, expiry)
    if lot is None:
        return None, LOT_UNKNOWN
    return Plan(event, lot, from_column, future.close, expiry, pushed, strikes, chains[expiry]), ""


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
) -> tuple[EventMarket | None, str]:
    """The event's market, or the reason it is left out: K0 no longer listed on R, or (current format) the contract's
    lot changed or is missing on R. Only listed strikes, the lot column and contracts traded are read from R."""
    exit_chain = exit_chain or {}
    if not any(strike == plan.strikes.k0 for strike, _ in exit_chain):
        return None, CORPORATE_ACTION
    if plan.lot_from_column:
        on_r = chain_lot(exit_chain, plan.strikes.k0)
        if on_r is None:
            return None, LOT_UNKNOWN_ON_R
        if on_r != plan.lot:
            return None, CORPORATE_ACTION
    found = EventMarket(
        symbol=plan.event.symbol,
        reaction=plan.event.reaction,
        sector=sector,
        lot=plan.lot,
        strikes=plan.strikes,
        entry=plan.entry,
        exit=exit_chain,
        previous=previous_chain or {},
    )
    return found, ""
