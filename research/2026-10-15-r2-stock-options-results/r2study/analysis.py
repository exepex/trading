"""The whole study on its inputs (PROTOCOL.md sections 3-9 with amendments 1 and 2): one function, no I/O of its own."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .clusters import cluster_key
from .descriptive import eligible_stocks_by_year, plan_lines, results_date_coverage, stage0
from .evaluate import evaluate
from .events import Event, Filings, Meeting, build_events
from .lots import LotSizes, validate_derivation
from .markets import CORPORATE_ACTION, Plan, market, needed_days, plan_event, screen_lots
from .moves import Correlation, correlation_events, market_adjusted_move, within_week_correlation
from .reading import DayFile, FileReader
from .rules import DECISION_START, PERIOD_START
from .sessions import Sessions
from .sources import CorporateActions, SymbolNames
from .spreads import QuotedLeg, SpreadModel
from .stages import CANNOT, Scored, decide, score_structure
from .structures import STRUCTURES


@dataclass
class Inputs:
    sessions: Sessions
    current: DayFile  # the current-format file of a session (None before 2024)
    legacy: DayFile  # the legacy-format file (None after 5 Jul 2024)
    nifty: Callable[[date], float | None]  # NIFTY 50 close of a session
    meetings: list[Meeting]
    filing_times: dict[str, list[datetime]]
    sectors: dict[str, str]
    names: SymbolNames
    actions: CorporateActions
    charges: dict
    snapshot: list[QuotedLeg] | None
    workers: int = 0


def run(inputs: Inputs) -> dict:
    s = inputs.sessions
    reader = FileReader(inputs.names, inputs.workers)
    current = reader.summaries(s.days, inputs.current)
    legacy = reader.summaries([d for d in s.days if d not in current or d.year == 2024], inputs.legacy)

    def summary(day: date):
        return current.get(day) or legacy.get(day)

    overlap = sorted(set(current) & set(legacy))
    validation = validate_derivation(s, overlap, current.get, legacy.get)
    lots = LotSizes(s, current.get, legacy.get, validation["valid"])
    meetings = [Meeting(inputs.names(m.symbol, m.day), m.day, m.text) for m in inputs.meetings]
    filings = Filings(_canonical_filings(inputs.filing_times, inputs.names))
    events, counts = build_events(meetings, filings, s, lambda sym, d: bool(summary(d) and summary(d).is_fo_stock(sym)))
    events = [e for e in events if PERIOD_START <= e.reaction <= s.last]
    kept, lot_counts = screen_lots(events, lots, inputs.actions)
    counts.update(lot_counts)
    plans = _plans(kept, reader, inputs, s, summary, counts)
    markets = _markets(plans, reader, inputs, s, counts)
    spreads = SpreadModel(inputs.snapshot) if inputs.snapshot else None
    correlation = _correlation(events, lots, summary, inputs)
    scored = _score(markets, inputs.charges, spreads)
    decision_events = [e for e in events if e.reaction >= DECISION_START]
    window = (DECISION_START, s.last)
    results = [score_structure(n, [x for x in v if x.reaction >= DECISION_START], window, correlation.rho_abs)
               for n, v in scored.items()]  # fmt: skip
    earlier = [score_structure(n, [x for x in v if x.reaction < DECISION_START],
                               (PERIOD_START, DECISION_START - timedelta(days=1)), correlation.rho_abs)
               for n, v in scored.items()]  # fmt: skip
    coverage = results_date_coverage(meetings, {d: summary(d) for d in s.days}, s, DECISION_START)
    zero = stage0(
        coverage, sum(1 for e in decision_events if lots.lot(e.symbol, e.entry) is None), len(decision_events)
    )
    answer = decide(results, spreads is not None) if zero["passes"] else {"answer": CANNOT, "stage": "stage 0"}
    analysed = [m for m in markets if m.reaction >= DECISION_START]
    return {
        "answer": answer,
        "stage0": {"coverage": coverage, **zero, "lot_validation": validation},
        "events": _event_counts(events, decision_events, analysed, counts),
        "structures": results,
        "structures_2019_sep_2024": earlier,
        "correlation": correlation,
        "spreads": spreads,
        "descriptive": {
            **plan_lines(plans, inputs.sectors),
            "eligible_stocks_by_year": eligible_stocks_by_year(current | legacy),
        },
        "window": window,
        "decision_kish_all": _kish_all(analysed, correlation),
    }  # fmt: skip


def _canonical_filings(times: dict[str, list[datetime]], names: SymbolNames) -> dict[str, list[datetime]]:
    out: dict[str, list[datetime]] = defaultdict(list)
    for symbol, moments in times.items():
        for moment in moments:
            out[names(symbol, moment.date())].append(moment)
    return out


def _plans(kept, reader: FileReader, inputs: Inputs, s: Sessions, summary, counts: Counter) -> list[Plan]:
    by_entry: dict[date, list] = defaultdict(list)
    for event, lot in kept:
        by_entry[event.entry].append((event, lot))
    plans = []
    needs = {day: {e.symbol for e, _ in items} for day, items in by_entry.items()}
    for day, chains in reader.chains(needs, lambda d: inputs.current(d) or inputs.legacy(d)):
        for event, lot in by_entry[day]:
            plan, reason = plan_event(event, lot, summary(day), chains.get(event.symbol, {}), s)
            if plan is None:
                counts[reason] += 1
            else:
                plans.append(plan)
    return plans


def _markets(plans: list[Plan], reader: FileReader, inputs: Inputs, s: Sessions, counts: Counter) -> list:
    exits, previous = {}, {}
    as_exit, as_previous = defaultdict(list), defaultdict(list)
    for i, plan in enumerate(plans):
        as_exit[plan.event.reaction].append(i)
        as_previous[s.before(plan.event.entry)].append(i)
    for day, chains in reader.chains(needed_days(plans, s), lambda d: inputs.current(d) or inputs.legacy(d)):
        for found, indices in ((exits, as_exit[day]), (previous, as_previous[day])):
            for i in indices:
                found[i] = chains.get(plans[i].event.symbol, {}).get(plans[i].expiry)
    markets = []
    for i, plan in enumerate(plans):
        found = market(plan, inputs.sectors.get(plan.event.symbol), exits.get(i), previous.get(i))
        if found is None:
            counts[CORPORATE_ACTION] += 1
        else:
            markets.append(found)
    return markets


def _correlation(events: list[Event], lots: LotSizes, summary, inputs: Inputs) -> Correlation:
    """2019-2021 moves, leaving out events whose derived lot changes from entry to R (an adjustment)."""
    moves = []
    for event in correlation_events(events):
        entry, reaction = summary(event.entry), summary(event.reaction)
        before, after = lots.derived(event.symbol, event.entry), lots.derived(event.symbol, event.reaction)
        if entry is None or reaction is None or (before and after and before != after):
            continue
        n0, n1 = inputs.nifty(event.entry), inputs.nifty(event.reaction)
        m = market_adjusted_move(event, entry, reaction, n0 or 0.0, n1 or 0.0)
        if m is not None:
            moves.append((cluster_key(inputs.sectors.get(event.symbol), event.reaction), m))
    return within_week_correlation(moves)


def _score(markets: list, charges: dict, spreads) -> dict[str, list[Scored]]:
    scored: dict[str, list[Scored]] = {st.name: [] for st in STRUCTURES}
    for m in markets:
        for structure in STRUCTURES:
            scored[structure.name].append(Scored(evaluate(structure, m, charges, spreads), m.reaction, m.sector))
    return scored


def _event_counts(events: list[Event], decision: list[Event], analysed: list, counts: Counter) -> dict:
    return {
        "events_2019_on": len(events),
        "decision_window_events": len(decision),
        "decision_window_analysed": len(analysed),
        "with_filing_time": sum(1 for e in events if e.filed_at is not None),
        "left_out_by_reason": dict(sorted(counts.items())),
    }


def _kish_all(analysed: list, correlation: Correlation) -> dict:
    from .clusters import cluster_sizes, kish_count

    keys = [cluster_key(m.sector, m.reaction) for m in analysed]
    return {"clusters": len(set(keys)), "kish": kish_count(cluster_sizes(keys), correlation.rho_abs)}
