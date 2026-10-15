"""Protocol v4 scoring as a service (story G8): per question, every forecaster's scores and each non-baseline
forecaster's comparison with the primary baseline; and each registered member's comparison for a look. V4 and V5 are
not started here (their outcomes need A16's weekly ATM quotes and the expiry settlement wiring)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from ...constants import V4_BASELINE_BASE_RATE, V4_RV_BELOW_WEEKLY_IV, V5_INSIDE_STRADDLE
from ...forecast_v4.terms import HORIZON_SESSIONS, POINT_QUESTIONS
from .comparison import Comparison, compare, paired_rows, seed_word
from .inputs import ForecastValue, Outcome, V4ForecastSource, V4OutcomeSource
from .primary import primary_names, primary_values
from .records import Registration, SlotRegistry
from .scores import point_scores, probability_scores

QUESTIONS = tuple(HORIZON_SESSIONS)  # the protocol's order
NOT_STARTED = frozenset({V4_RV_BELOW_WEEKLY_IV, V5_INSIDE_STRADDLE})
STATUS_NOT_STARTED, STATUS_NO_DATA, STATUS_SCORED = "not started", "not enough data yet", "scored"


@dataclass
class QuestionReport:
    question: str
    status: str
    scores: dict[str, object] = field(default_factory=dict)  # forecaster -> PointScores / ProbabilityScores / None
    comparisons: list[Comparison] = field(default_factory=list)
    live_forecasts: int = 0  # rows labelled live, across the question's forecasters


class V4Scoring:
    def __init__(self, forecasts: V4ForecastSource, outcomes: V4OutcomeSource, registry: SlotRegistry):
        self.forecasts, self.outcomes, self.registry = forecasts, outcomes, registry

    def question_report(self, question: str) -> QuestionReport:
        if question in NOT_STARTED:
            return QuestionReport(question, STATUS_NOT_STARTED)
        names = self.forecasters(question)
        if not names:
            return QuestionReport(question, STATUS_NO_DATA)
        outcomes, baseline = self.outcomes.outcomes(question), primary_values(question, self.forecasts)
        values = {name: self.forecasts.values(question, name) for name in names}
        slots = {r.forecaster: slot for (q, slot), r in self.registry.registered().items() if q == question}
        report = QuestionReport(question, STATUS_SCORED)
        report.live_forecasts = sum(v.live and v.value is not None for vs in values.values() for v in vs.values())
        base_rate = self.forecasts.values(question, V4_BASELINE_BASE_RATE)
        report.scores = {name: _scores(question, values[name], outcomes, base_rate) for name in names}
        for name in (n for n in names if n not in primary_names(question)):
            report.comparisons.append(self._compare(question, name, values[name], baseline, outcomes, slots.get(name)))
        return report

    def forecasters(self, question: str) -> list[str]:
        return [] if question in NOT_STARTED else self.forecasts.forecasters(question)

    def member_comparisons(self, counted_after: date | None) -> dict[tuple[str, str], Comparison]:
        """Each registered member: its slot's forecaster against the question's primary baseline. After the freeze
        (`counted_after`: its day) only live rows of later forecast days count (protocol section 8); back-fill and
        earlier live rows never do, and misses count from the slot's `effective_start` (never before the day after
        the freeze), even before its first forecast. None (before the freeze, exploratory): every row, misses from
        the first forecast."""
        found = {}
        for (question, slot), registration in self.registry.registered().items():
            outcomes = self.outcomes.outcomes(question)
            baseline = _counted(primary_values(question, self.forecasts), counted_after)
            values = _counted(self.forecasts.values(question, registration.forecaster), counted_after)
            found[(question, slot)] = self._compare(question, registration.forecaster, values, baseline, outcomes,
                                                    slot, _miss_start(registration, counted_after))  # fmt: skip
        return found

    @staticmethod
    def _compare(question, forecaster, values, baseline, outcomes, slot, miss_start=None) -> Comparison:
        rows = paired_rows(values, baseline, outcomes)
        return compare(question, forecaster, " / ".join(sorted(primary_names(question))), rows, outcomes,
                       seed_word(question, slot, forecaster), miss_start)  # fmt: skip


def _counted(values: dict[date, ForecastValue], after: date | None) -> dict[date, ForecastValue]:
    return values if after is None else {day: v for day, v in values.items() if v.live and day > after}


def _miss_start(registration: Registration, after: date | None) -> date | None:
    """After the freeze, the slot's declared `effective_start`, never earlier than the day after the freeze (no
    earlier day can count); before the freeze, None (exploratory: misses from the first forecast in the rows)."""
    if after is None:
        return None
    return max(registration.effective_start, after + timedelta(days=1))


def _scores(question: str, values: dict[date, ForecastValue], outcomes: dict[date, Outcome],
            base_rate: dict[date, ForecastValue]):  # fmt: skip
    scored = {
        day: (v.value, outcomes[day].value)
        for day, v in values.items()
        if v.value is not None and day in outcomes and outcomes[day].value is not None and not outcomes[day].void
    }
    if question in POINT_QUESTIONS:
        return point_scores(list(scored.values()))
    base = [(p, base_rate[day].value, o) for day, (p, o) in scored.items()
            if day in base_rate and base_rate[day].value is not None]  # fmt: skip
    return probability_scores(list(scored.values()), base)
