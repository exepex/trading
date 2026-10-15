"""The role-value report of one book and period (story F9a): the rows checked, each scored pair valued, every unit
scored and, at a review, judged; open pairs and excluded rows listed apart; the control roles' counts. Every figure
carries the protocol label (S1 `reporting_per_version`)."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date

from ..scoreboard.matched_days import CommonSet
from ..scoreboard.standard_unit import StandardUnit
from .checks import checked
from .controls import ControlCounts
from .cost import ConsultedDay, MonthAllocation, cost_per_opportunity
from .records import DecisionRecords
from .role_set import RoleSet
from .rows import SCORED, PairedDecisionSource, PairedRow
from .score import Opportunity, UnitScore, score_unit
from .valuation import SCORED as PAIR_SCORED
from .valuation import WAITING, value_pair
from .verdict import verdicts

PILOT = "pilot, before the common start"


@dataclass(frozen=True)
class Period:
    book: str
    first: date
    last: date
    common_start: date
    review: bool = False


@dataclass
class RoleValueResult:
    period: Period
    protocol: str
    scores: list[UnitScore] = field(default_factory=list)
    verdicts: dict[str, str] = field(default_factory=dict)
    open_pairs: list[str] = field(default_factory=list)
    excluded: dict[str, int] = field(default_factory=dict)
    controls: ControlCounts | None = None
    rows: int = 0


@dataclass(frozen=True)
class RoleValueInputs:
    source: PairedDecisionSource
    role_set_of: Callable[[str, str], RoleSet]  # (book, version) -> its units
    real: DecisionRecords
    shadow: DecisionRecords
    packs: Callable[[date], CommonSet | None]
    unit: StandardUnit
    run_log_snapshots: Mapping[date, str]
    allocation_of: MonthAllocation
    usage_of: Callable[[str], Sequence[Mapping]]  # F8's ledger rows of a month
    review_days: Callable[[date, date], Sequence[date]]  # (common start, through) -> scheduled reviews
    controls: Callable[[str, date, date], ControlCounts]
    protocol: str


class RoleValueReport:
    def __init__(self, inputs: RoleValueInputs):
        self.i = inputs

    def build(self, period: Period) -> RoleValueResult:
        book = period.book
        rows = checked(self.i.source.rows(book), lambda v: self.i.role_set_of(book, v), self.i.run_log_snapshots,
                       period.common_start)  # fmt: skip
        rows = [r for r in rows if period.first <= r.day <= period.last]
        result = RoleValueResult(period, self.i.protocol, rows=len(rows))
        pilot = [r for r in rows if r.day < period.common_start]  # pilot evidence, never scored (S1)
        if pilot:
            result.excluded[PILOT] = len(pilot)
        rows = [r for r in rows if r.day >= period.common_start]
        found: dict[str, list[Opportunity]] = {}
        for row in rows:
            self._pair(row, period.last, result, found)
        days = [ConsultedDay(r.day, r.consulted_units) for r in rows]
        units = sorted({u for r in rows for u in self.i.role_set_of(book, r.version).unit_ids})
        for unit in units:
            cost = cost_per_opportunity(unit, days, book, self.i.allocation_of, self.i.usage_of)
            result.scores.append(score_unit(unit, found.get(unit, []), cost))
        reviews = self.i.review_days(period.common_start, period.last)
        result.verdicts = verdicts(result.scores, period.review, period.last, reviews)
        result.controls = self.i.controls(book, period.first, period.last)
        return result

    def _pair(self, row: PairedRow, on: date, result: RoleValueResult, found: dict[str, list[Opportunity]]) -> None:
        if row.status != SCORED or not row.consulted:
            reason = row.status if row.status != SCORED else "card not consulted (not applicable)"
            result.excluded[reason] = result.excluded.get(reason, 0) + 1
            return
        real = self.i.real.records(row.book, row.day, row.real_decision_id)
        shadow = self.i.shadow.records(row.book, row.day, row.shadow_decision_id)
        value = value_pair(real, shadow, self.i.packs(row.day), row.day, self.i.unit, on)
        if value.status == WAITING:
            result.open_pairs.append(f"{row.day} {row.unit}: {value.note}")
        elif value.status != PAIR_SCORED:
            reason = f"not scored: {value.note}"
            result.excluded[reason] = result.excluded.get(reason, 0) + 1
        else:
            opportunity = Opportunity(row.day, value.difference, value.changed, value.max_loss_difference)
            found.setdefault(row.unit, []).append(opportunity)
