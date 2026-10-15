"""The run's steps after the events: plans on the entry session, markets on R, the 2019-2021 moves and the scores.

Every event left out is recorded with its reason (amendment 2: never silently dropped)."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date

from .clusters import cluster_key
from .evaluate import EventMarket, evaluate
from .events import Event
from .lots import LegacyLots
from .markets import Plan, market, needed_days, plan_event
from .moves import Correlation, correlation_events, market_adjusted_move, within_week_correlation
from .reading import FileReader
from .sessions import Sessions
from .stages import Scored
from .structures import STRUCTURES

NO_PREVIOUS_CHAIN = "no previous-session row for the chosen expiry (legs at 0 contracts)"
MOVE_NO_FILE, MOVE_ADJUSTED, MOVE_NO_PRICE = (
    "no F&O file on entry or R",
    "derived lot changed from entry to R",
    "no same-expiry future close or no NIFTY close",
)


class Left:
    """Events left out, each with its reason."""

    def __init__(self):
        self.events: list[tuple[Event, str]] = []

    def add(self, event: Event, reason: str) -> None:
        self.events.append((event, reason))

    def counts(self, first: date | None = None) -> Counter:
        return Counter(r for e, r in self.events if first is None or e.reaction >= first)


def plans(events, reader: FileReader, read, s: Sessions, summary, legacy: LegacyLots | None, left: Left) -> list[Plan]:
    by_entry: dict[date, list[Event]] = defaultdict(list)
    for event in events:
        by_entry[event.entry].append(event)
    out = []
    needs = {day: {e.symbol for e in items} for day, items in by_entry.items()}
    for day, chains in reader.chains(needs, read):
        for event in by_entry[day]:
            plan, reason = plan_event(event, summary(day), chains.get(event.symbol, {}), s, legacy)
            if plan is None:
                left.add(event, reason)
            else:
                out.append(plan)
    return out


def markets(found: list[Plan], reader: FileReader, read, s: Sessions, sectors, left: Left, notes: Counter) -> list:
    exits, previous = {}, {}
    as_exit, as_previous = defaultdict(list), defaultdict(list)
    for i, plan in enumerate(found):
        as_exit[plan.event.reaction].append(i)
        as_previous[s.before(plan.event.entry)].append(i)
    for day, chains in reader.chains(needed_days(found, s), read):
        for store, indices in ((exits, as_exit[day]), (previous, as_previous[day])):
            for i in indices:
                store[i] = chains.get(found[i].event.symbol, {}).get(found[i].expiry)
    out: list[EventMarket] = []
    for i, plan in enumerate(found):
        if previous.get(i) is None:
            notes[NO_PREVIOUS_CHAIN] += 1
        result, reason = market(plan, sectors.get(plan.event.symbol), exits.get(i), previous.get(i))
        if result is None:
            left.add(plan.event, reason)
        else:
            out.append(result)
    return out


def correlation(events: list[Event], legacy: LegacyLots, summary, nifty, sectors) -> tuple[Correlation, Counter]:
    """2019-2021 moves; an event whose derived same-expiry lot changes from entry to R is left out (an adjustment)."""
    moves, dropped = [], Counter()
    for event in correlation_events(events):
        entry, reaction = summary(event.entry), summary(event.reaction)
        if entry is None or reaction is None:
            dropped[MOVE_NO_FILE] += 1
            continue
        future = entry.near_future(event.symbol, on_or_after=event.reaction)
        if future is not None:
            before = legacy.derived(event.symbol, event.entry, future.expiry)
            after = legacy.derived(event.symbol, event.reaction, future.expiry)
            if before and after and before != after:
                dropped[MOVE_ADJUSTED] += 1
                continue
        n0, n1 = nifty(event.entry), nifty(event.reaction)
        m = market_adjusted_move(event, entry, reaction, n0, n1) if n0 and n1 else None
        if m is None:
            dropped[MOVE_NO_PRICE] += 1
            continue
        moves.append((cluster_key(sectors.get(event.symbol), event.reaction), m))
    return within_week_correlation(moves), dropped


def score(found: list[EventMarket], charges: dict, spreads) -> dict[str, list[Scored]]:
    scored: dict[str, list[Scored]] = {st.name: [] for st in STRUCTURES}
    for m in found:
        for structure in STRUCTURES:
            scored[structure.name].append(Scored(evaluate(structure, m, charges, spreads), m.reaction, m.sector))
    return scored
