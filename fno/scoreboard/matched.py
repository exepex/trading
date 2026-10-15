"""Scoreboard A's scores (story S3, expected design 3): each take's one-lot result, a book's series by decision day and
its net per unit of maximum loss at entry (S1's scoreboard A measure: Σ net ÷ Σ maximum loss, no daily marks), and the
paired daily rupee difference between two books. Bounds and p-values come from S2's moving-block resampler: the
per-book series is (net, maximum loss) by day; a pair's series has risk 1 on every day, so its ratio is the mean
difference. A day with an open take ends a series (open results are cut, never counted as 0)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from ..desk.pricing import DeskLeg
from ..research_engine.structures import Leg
from .book_board import full_months
from .matched_actions import SKIP, TAKE
from .matched_days import BookDay
from .series import DailySeries
from .standard_unit import CLOSED, MAX_LOSS_UNKNOWN, NOT_FILLED, OPEN, StandardResult, StandardUnit
from .uncertainty import p_value, uncertainty

Results = Mapping[tuple[str, date, str], StandardResult]  # (book, day, opportunity ID) -> one-lot result


@dataclass(frozen=True)
class DayScore:
    day: date
    net: float
    risk: float
    open: bool


def unit_legs(record: Mapping, expiry: date) -> list[DeskLeg]:
    return [DeskLeg(leg["contract"], expiry, Leg(float(leg["strike"]), leg["type"], int(leg["side"])))
            for leg in record["structure"]["legs"]]  # fmt: skip


def value_takes(days: Iterable[BookDay], entries: Mapping[tuple[date, str], Mapping], unit: StandardUnit,
                on: date) -> dict[tuple[str, date, str], StandardResult]:  # fmt: skip
    """Every take's one-lot result; `entries` holds each day's common-set entry (expiry, exit day) by opportunity."""
    results = {}
    for book_day in days:
        for opportunity_id, action in book_day.actions.items():
            if action.kind == TAKE:
                entry = entries[(book_day.day, opportunity_id)]
                legs = unit_legs(action.record, date.fromisoformat(entry["expiry"]))
                exit_day = date.fromisoformat(entry["exit_day"])
                results[(book_day.book, book_day.day, opportunity_id)] = unit.value(legs, book_day.day, exit_day, on)
    return results


def day_score(book_day: BookDay, results: Results) -> DayScore:
    net = risk = 0.0
    is_open = False
    for opportunity_id, action in book_day.actions.items():
        result = results.get((book_day.book, book_day.day, opportunity_id)) if action.kind == TAKE else None
        if result is not None and result.status == OPEN:
            is_open = True
        elif result is not None and result.status == CLOSED:
            net, risk = net + result.net, risk + result.max_loss
    return DayScore(book_day.day, net, risk, is_open)


def scored_days(days: Sequence[BookDay], results: Results) -> list[DayScore]:
    """The observed days up to the last one whose takes have all closed (design 3: series days)."""
    scores = []
    for book_day in sorted((d for d in days if d.observed), key=lambda d: d.day):
        score = day_score(book_day, results)
        if score.open:
            break
        scores.append(score)
    return scores


def series_of(scores: Sequence[DayScore]) -> DailySeries:
    return DailySeries(tuple(s.day for s in scores), tuple(s.net for s in scores), tuple(s.risk for s in scores))


def counts(days: Sequence[BookDay], results: Results) -> dict:
    statuses = [results[(d.book, d.day, o)].status for d in days for o, a in d.actions.items() if a.kind == TAKE]
    not_observed: dict[str, int] = {}
    for book_day in days:
        if not book_day.observed:
            not_observed[book_day.observed_reason] = not_observed.get(book_day.observed_reason, 0) + 1
        for action in book_day.actions.values():
            if action.kind not in (TAKE, SKIP):
                not_observed[action.reason] = not_observed.get(action.reason, 0) + 1
    return {
        "observed_days": sum(d.observed for d in days),
        "takes": {s: statuses.count(s) for s in (CLOSED, OPEN, NOT_FILLED, MAX_LOSS_UNKNOWN)},
        "skips": sum(a.kind == SKIP for d in days for a in d.actions.values()),
        "not_observed": dict(sorted(not_observed.items())),
    }


def judged(series: DailySeries, positions: int) -> dict:
    """S1's uncertainty criterion on a series (S2's function, so the sample rule and the bound are S2's) and its
    one-sided p-value, the input to Holm across a review's claims."""
    first, last = (series.days[0], series.days[-1]) if series.days else (None, None)
    months = full_months(first, last) if first else 0
    verdict, p = uncertainty(series, positions, months), p_value(series)
    return {
        "days": len(series.days), "net_rs": round(series.total_net, 2), "risk_rs": round(series.risk_days, 2),
        "ratio": None if series.net_per_risk is None else round(series.net_per_risk, 6),
        "lower_bound": None if verdict.lower_bound is None else round(verdict.lower_bound, 6),
        "p_value": None if p is None else round(p, 6), "sample_met": verdict.sample_met,
        "claim_allowed": verdict.claim_allowed, "reason": verdict.reason,
    }  # fmt: skip


def pair_series(first: Sequence[DayScore], second: Sequence[DayScore]) -> DailySeries:
    """The daily one-lot net difference on the days both books are scored, with risk 1 a day."""
    other = {s.day: s.net for s in second}
    days = [s for s in first if s.day in other]
    return DailySeries(tuple(s.day for s in days), tuple(s.net - other[s.day] for s in days), tuple(1.0 for _ in days))
