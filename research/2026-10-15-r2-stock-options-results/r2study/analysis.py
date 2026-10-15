"""The whole study on its inputs (PROTOCOL.md sections 3-9 with amendments 1 and 2): one function, no I/O of its own."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from . import steps
from .clusters import cluster_key, cluster_sizes, kish_count
from .descriptive import eligible_stocks_by_year, plan_lines, results_date_coverage, stage0
from .events import Filings, Meeting, build_events
from .lots import LegacyLots, validate_derivation
from .markets import CORPORATE_ACTION, LOT_UNKNOWN, screen_actions
from .reading import DayFile, FileReader
from .rules import DECISION_START, PERIOD_START
from .sessions import Sessions
from .snapshot_legs import SnapshotLegs
from .sources import CorporateActions, SymbolNames
from .spreads import SpreadModel
from .stages import CANNOT, decide, score_structure

Filed = tuple[datetime, date]
OUTSIDE_PERIOD = "reaction session before 1 Jan 2019"


class MissingFile(RuntimeError):
    """A session has no readable F&O file: the run stops rather than count it as a wrong exclusion."""


@dataclass
class Inputs:
    sessions: Sessions
    current: DayFile  # the current-format file of a session (None before 2024)
    legacy: DayFile  # the legacy-format file (None after 5 Jul 2024)
    nifty: Callable[[date], float | None]  # NIFTY 50 close of a session
    meetings: list[Meeting]
    filing_times: dict[str, list[Filed]]  # symbol -> (filing time, period end)
    sectors: dict[str, str]
    names: SymbolNames
    actions: CorporateActions
    charges: dict
    snapshot: SnapshotLegs | None  # rebuilt from the raw Drive file; None when no snapshot was taken
    workers: int = 0


def run(inputs: Inputs) -> dict:
    s = inputs.sessions
    reader = FileReader(inputs.names, inputs.workers)
    current = reader.summaries(s.days, inputs.current)
    legacy = reader.summaries([d for d in s.days if d not in current or d.year == 2024], inputs.legacy)
    missing = [d for d in s.days if d not in current and d not in legacy]
    if missing:
        raise MissingFile(f"{len(missing)} sessions without a readable F&O file, first {missing[:3]}")

    def summary(day: date):
        return current.get(day) or legacy.get(day)

    def read(day: date):
        return inputs.current(day) or inputs.legacy(day)

    validation = validate_derivation(s, sorted(set(current) & set(legacy)), current.get, legacy.get)
    legacy_rule = LegacyLots(s, legacy.get)
    meetings = [Meeting(inputs.names(m.symbol, m.day), m.day, m.text) for m in inputs.meetings]
    filings = Filings(_canonical_filings(inputs.filing_times, inputs.names))
    built, counts = build_events(meetings, filings, s, lambda sym, d: bool(summary(d) and summary(d).is_fo_stock(sym)))
    events = [e for e in built if PERIOD_START <= e.reaction <= s.last]
    counts[OUTSIDE_PERIOD] += len(built) - len(events)
    left, notes = steps.Left(), Counter()
    kept, _ = screen_actions(events, inputs.actions)
    for event in set(events) - set(kept):
        left.add(event, CORPORATE_ACTION)
    found_plans = steps.plans(kept, reader, read, s, summary, legacy_rule if validation["valid"] else None, left)
    found = steps.markets(found_plans, reader, read, s, inputs.sectors, left, notes)
    spreads = SpreadModel(inputs.snapshot.legs) if inputs.snapshot and inputs.snapshot.usable else None
    correlation, dropped = steps.correlation(events, legacy_rule, summary, inputs.nifty, inputs.sectors)
    scored = steps.score(found, inputs.charges, spreads)
    window = (DECISION_START, s.last)
    results = [score_structure(n, [x for x in v if x.reaction >= DECISION_START], window, correlation.rho_abs)
               for n, v in scored.items()]  # fmt: skip
    earlier = [score_structure(n, [x for x in v if x.reaction < DECISION_START],
                               (PERIOD_START, DECISION_START - timedelta(days=1)), correlation.rho_abs)
               for n, v in scored.items()]  # fmt: skip
    decision_events = [e for e in events if e.reaction >= DECISION_START]
    coverage = results_date_coverage(meetings, {d: summary(d) for d in s.days}, s, DECISION_START)
    zero = stage0(coverage, left.counts(DECISION_START)[LOT_UNKNOWN], len(decision_events))
    answer = decide(results, spreads is not None) if zero["passes"] else _cannot(zero)
    analysed = [m for m in found if m.reaction >= DECISION_START]
    return {
        "answer": answer,
        "stage0": {"coverage": coverage, **zero, "lot_validation": validation},
        "events": {
            "events_2019_on": len(events),
            "decision_window_events": len(decision_events),
            "decision_window_analysed": len(analysed),
            "decision_window_with_filed_at": _share([e.filed_at is not None for e in decision_events]),
            "left_out_before_events": dict(sorted(counts.items())),
            "left_out_all_years": dict(sorted(left.counts().items())),
            "left_out_decision_window": dict(sorted(left.counts(DECISION_START).items())),
            "notes": dict(notes),
        },
        "structures": results,
        "structures_2019_sep_2024": earlier,
        "correlation": correlation,
        "correlation_left_out": dict(dropped),
        "spreads": spreads,
        "snapshot": inputs.snapshot.record() if inputs.snapshot else None,
        "descriptive": {
            **plan_lines([p for p in found_plans if p.event.reaction >= DECISION_START], inputs.sectors),
            "all_years": plan_lines(found_plans, inputs.sectors),
            "eligible_stocks_by_year": eligible_stocks_by_year(current | legacy),
        },
        "window": window,
        "decision_kish_all": _kish_all(analysed, correlation.rho_abs),
    }


def _cannot(zero: dict) -> dict:
    return {"answer": CANNOT, "stage": "stage 0", "reason": "; ".join(zero["reasons"])}


def _share(flags: list[bool]) -> float | None:
    return sum(flags) / len(flags) if flags else None


def _canonical_filings(times: dict[str, list[Filed]], names: SymbolNames) -> dict[str, list[Filed]]:
    out: dict[str, list[Filed]] = defaultdict(list)
    for symbol, filed in times.items():
        for moment, period in filed:
            out[names(symbol, moment.date())].append((moment, period))
    return out


def _kish_all(analysed: list, rho_abs: float | None) -> dict:
    keys = [cluster_key(m.sector, m.reaction) for m in analysed]
    return {"clusters": len(set(keys)), "kish": kish_count(cluster_sizes(keys), rho_abs)}
