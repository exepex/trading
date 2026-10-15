"""Stage 0 and the descriptive lines every stage reports (PROTOCOL.md section 9, amendment 1 section D7)."""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from datetime import date

from .bhav import DaySummary
from .events import Meeting, is_results_meeting
from .rules import MAX_LOT_UNKNOWN_SHARE, MIN_RESULTS_DATE_COVERAGE, UNKNOWN_SECTOR
from .sessions import Sessions


def quarter(day: date) -> tuple[int, int]:
    return day.year, (day.month - 1) // 3 + 1


def complete_quarters(sessions: Sessions, first: date) -> list[tuple[date, date]]:
    """(first session, last session) of each calendar quarter from `first` that ended before the last session."""
    spans: dict[tuple[int, int], list[date]] = defaultdict(list)
    for day in sessions.days:
        if day >= first:
            spans[quarter(day)].append(day)
    last = quarter(sessions.last)
    return [(days[0], days[-1]) for key, days in sorted(spans.items()) if key < last]


def results_date_coverage(
    meetings: list[Meeting], summaries: dict[date, DaySummary], sessions: Sessions, first: date
) -> dict:
    """Share of stock-quarters (F&O-listed on the quarter's first and last session) with a results meeting in it."""
    with_results = {(m.symbol, quarter(m.day)) for m in meetings if is_results_meeting(m)}
    total = covered = 0
    for start, end in complete_quarters(sessions, first):
        for symbol in summaries[start].futures:
            if summaries[start].is_fo_stock(symbol) and summaries[end].is_fo_stock(symbol):
                total += 1
                covered += (symbol, quarter(start)) in with_results
    share = covered / total if total else 0.0
    return {"stock_quarters": total, "covered": covered, "share": share, "passes": share >= MIN_RESULTS_DATE_COVERAGE}


def stage0(coverage: dict, lot_unknown: int, events: int) -> dict:
    """Cannot answer (not NO) when results dates or lot sizes are too thin on the decision window."""
    lot_share = lot_unknown / events if events else 1.0
    reasons = []
    if not coverage["passes"]:
        reasons.append(f"results dates for {coverage['share']:.1%} of stock-quarters (< 80%)")
    if lot_share > MAX_LOT_UNKNOWN_SHARE:
        reasons.append(f"lot size unknown for {lot_share:.1%} of events (> 10%)")
    return {"lot_unknown_share": lot_share, "passes": not reasons, "reasons": reasons}


def quartiles(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    if len(values) == 1:
        return {"n": 1, "median": values[0]}
    q1, q2, q3 = statistics.quantiles(values, n=4)
    return {"n": len(values), "p25": q1, "median": q2, "p75": q3}


def by_year(rows: list[tuple[date, float]]) -> dict[int, dict]:
    years: dict[int, list[float]] = defaultdict(list)
    for day, value in rows:
        years[day.year].append(value)
    return {year: quartiles(values) for year, values in sorted(years.items())}


def eligible_stocks_by_year(summaries: dict[date, DaySummary]) -> dict[int, dict]:
    """Point-in-time F&O stocks: the median daily count and the distinct stocks seen, per year."""
    counts: dict[int, list[int]] = defaultdict(list)
    seen: dict[int, set[str]] = defaultdict(set)
    for day, summary in summaries.items():
        stocks = [s for s in summary.futures if summary.is_fo_stock(s)]
        counts[day.year].append(len(stocks))
        seen[day.year].update(stocks)
    return {y: {"median_daily": statistics.median(counts[y]), "distinct": len(seen[y])} for y in sorted(counts)}


def plan_lines(plans: list, sectors: dict[str, str]) -> dict:
    """Lot values, strike steps as % of price and pushes to the second month, by year of R; the `unknown` sector."""
    lot_values = [(p.event.reaction, p.lot * p.underlying) for p in plans]
    steps = [(p.event.reaction, 100 * p.strikes.up / p.underlying) for p in plans if p.strikes.up]
    pushed: dict[int, Counter] = defaultdict(Counter)
    for p in plans:
        pushed[p.event.reaction.year][p.pushed] += 1
    return {
        "lot_value_rs_by_year": by_year(lot_values),
        "strike_step_pct_by_year": by_year(steps),
        "pushed_share_by_year": {y: c[True] / (c[True] + c[False]) for y, c in sorted(pushed.items())},
        "unknown_sector_events": sum(1 for p in plans if p.event.symbol not in sectors),
        "unknown_sector_label": UNKNOWN_SECTOR,
    }
