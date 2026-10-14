"""One book on scoreboard B (story S2, S1's `common_start`, `pilot_evidence` and `segments`). Every trade opened
before the common start is pilot evidence, reported apart and never head-to-head. From the common start on, the head-
to-head figures hold only scored trades that were not overridden, overall and per D6 segment. Unscored and overridden
trades are shown in their own sections. A trade stays in the segment of the decision that opened it to its end.
Operating costs are the book's, not a version's: they enter the book-level sections only."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from .book_trades import NO_RECORD, OVERRIDDEN, ScoredTrade, Sessions
from .ports import AiCostAllocation
from .sections import section
from .series import costs_by_session, daily_series
from .uncertainty import uncertainty

PILOT = "pilot, not counted"
AI_AT_BOOK_LEVEL = "charged at book level only (overall, pilot, head-to-head)"
COMMON_START_NOT_REACHED = "pilot, not counted: common start not reached, every figure is pilot evidence"


@dataclass(frozen=True)
class BookInputs:
    book: str
    trades: tuple[ScoredTrade, ...]
    operating_costs: tuple[dict, ...]  # C1's rows
    first: date  # the account's first session
    on: date


def full_months(first: date, last: date) -> int:
    """Whole calendar months from the month after `first` (unless it is the 1st) to the month of `last` if complete."""
    start = (first.year, first.month) if first.day == 1 else (first.year + (first.month == 12), first.month % 12 + 1)
    months = (last.year - start[0]) * 12 + last.month - start[1]
    return max(months, 0)


class BookBoard:
    def __init__(self, sessions: Sessions, ai: AiCostAllocation):
        self.sessions, self.ai = sessions, ai

    def build(self, inputs: BookInputs, common_start: date | None) -> dict:
        monthly = _monthly(inputs.operating_costs)
        whole = (inputs.first, inputs.on)
        board = {"overall": self._section(inputs, inputs.trades, inputs.first, inputs.on, monthly, False, whole)}
        if common_start is None or common_start > inputs.on:
            board["pilot"] = board["overall"] | {"label": COMMON_START_NOT_REACHED}
            return board | {"head_to_head": None, "unscored": None, "overridden": None}
        pilot = [t for t in inputs.trades if t.opened_on < common_start]
        later = [t for t in inputs.trades if t.opened_on >= common_start]
        before = {m: v for m, v in monthly.items() if m < common_start.strftime("%Y-%m")}
        pilot_ai = (inputs.first, common_start - timedelta(days=1))  # AI periods never overlap (judge 87)
        board["pilot"] = self._section(inputs, pilot, inputs.first, inputs.on, before, False, pilot_ai) | {
            "label": PILOT
        }
        scored = [t for t in later if t.group not in (NO_RECORD, OVERRIDDEN)]
        after = {m: v for m, v in monthly.items() if m >= common_start.strftime("%Y-%m")}
        board["head_to_head"] = self._section(
            inputs, scored, common_start, inputs.on, after, True, (common_start, inputs.on)
        )
        board["head_to_head"]["segments"] = {
            label: self._section(inputs, [t for t in scored if t.group == label], common_start, inputs.on, {}, True)
            for label in sorted({t.group for t in scored})
        }
        for name in (NO_RECORD, OVERRIDDEN):
            board[name] = self._section(
                inputs, [t for t in later if t.group == name], common_start, inputs.on, {}, False
            )
        return board

    def _section(
        self, inputs: BookInputs, trades: Sequence[ScoredTrade], first: date, last: date, monthly: dict, judged: bool,
        ai_period: tuple[date, date] | None = None,
    ) -> dict:  # fmt: skip
        """`ai_period`: the days whose allocated AI cost this section carries; None for segments, unscored and
        overridden trades, whose AI cost stays at book level, so no rupee is counted twice."""
        sessions = self.sessions(first, last)
        costs = costs_by_session(monthly, sessions)
        series = daily_series(trades, costs, sessions)
        positions = sum(t.completed and t.line is not None for t in trades)
        judged_by = uncertainty(series, positions, full_months(first, last)) if judged else None
        if ai_period is None:
            board = section(trades, series, sum(costs.values()), 0.0, judged_by, first, last)
            return board | {"ai_cost_allocated_rs": AI_AT_BOOK_LEVEL}
        ai = self.ai.allocated(inputs.book, *ai_period)
        return section(trades, series, sum(costs.values()), ai, judged_by, first, last)


def _monthly(rows: Sequence[dict]) -> dict[str, float]:
    months: dict[str, float] = {}
    for row in rows:
        months[row["month"]] = months.get(row["month"], 0.0) + float(row["amount_rs"])
    return dict(sorted(months.items()))
