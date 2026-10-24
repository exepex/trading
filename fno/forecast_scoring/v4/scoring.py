"""Protocol v4 scoring as a service (story G8): per question, every forecaster's scores and each non-baseline
forecaster's comparison with the primary baseline; and each registered member's comparison for a look. Every question
is scored the same way once it has forecaster rows ("not enough data yet" before; V4 and V5 since story G7b
completion, part e). V2's and V3's intraday versions (part f, protocol 1.1) are their own reported series: the
question's forecaster rows, primary baseline, loss and block, against the intraday outcome, with a seed word of their
own, never a member. The report scores the live rows and the back-fill rows (the close stands in for the 14:30 pack)
as two cohorts, never pooled (G10)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from ...constants import V4_BASELINE_BASE_RATE, V4_COHORT_CLOSE_PROXY, V4_COHORT_LIVE
from ...forecast_v4.terms import HORIZON_SESSIONS, POINT_QUESTIONS
from ...forecast_v4_rules.intraday_series import INTRADAY_SERIES, RATIO_INTRADAY, SERIES_RATIO_MEASURE, question_of
from .comparison import Comparison, compare, paired_rows, seed_word
from .inputs import ForecastValue, Outcome, V4ForecastSource, V4OutcomeSource
from .primary import primary_names, primary_values
from .records import Registration, SlotRegistry
from .scores import point_scores, probability_scores

QUESTIONS = (*HORIZON_SESSIONS, *INTRADAY_SERIES)  # the protocol's order, then part f's reported series
STATUS_NO_DATA, STATUS_SCORED = "not enough data yet", "scored"
COHORTS = (V4_COHORT_CLOSE_PROXY, V4_COHORT_LIVE)


@dataclass
class Cohort:
    """One cohort's forecasters (only those with a row in it), their scores and their comparisons."""

    scores: dict[str, object] = field(default_factory=dict)  # forecaster -> PointScores / ProbabilityScores / None
    comparisons: list[Comparison] = field(default_factory=list)


@dataclass
class QuestionReport:
    question: str
    status: str
    cohorts: dict[str, Cohort] = field(default_factory=dict)  # COHORTS -> its scores and comparisons
    live_forecasts: int = 0  # rows labelled live, across the question's forecasters


class V4Scoring:
    def __init__(self, forecasts: V4ForecastSource, outcomes: V4OutcomeSource, registry: SlotRegistry):
        self.forecasts, self.outcomes, self.registry = forecasts, outcomes, registry

    def question_report(self, question: str) -> QuestionReport:
        """`question` is a protocol question or a part f series key (its forecasts are its question's)."""
        names = self.forecasters(question)
        outcomes = self.outcomes.outcomes(question) if names else {}
        if not names or (question in INTRADAY_SERIES and not outcomes):
            return QuestionReport(question, STATUS_NO_DATA)  # a part f series starts at its first live window
        values = {name: self._started(question, self.forecasts.values(question_of(question), name), outcomes)
                  for name in names}  # fmt: skip
        report = QuestionReport(question, STATUS_SCORED)
        report.live_forecasts = sum(v.live and v.value is not None for vs in values.values() for v in vs.values())
        report.cohorts = {
            cohort: self._cohort(question, values, outcomes, cohort == V4_COHORT_LIVE) for cohort in COHORTS
        }
        return report

    def _cohort(self, question: str, every: dict[str, dict[date, ForecastValue]], outcomes: dict[date, Outcome],
                live: bool) -> Cohort:  # fmt: skip
        asked = question_of(question)
        values = {name: rows for name, all_rows in every.items() if (rows := _in_cohort(all_rows, live))}
        baseline = _in_cohort(self._started(question, self._baseline(question), outcomes), live)
        base_rate = _in_cohort(self._started(question, self.forecasts.values(asked, V4_BASELINE_BASE_RATE), outcomes),
                               live)  # fmt: skip
        slots = {r.forecaster: slot for (q, slot), r in self.registry.registered().items() if q == question}
        cohort = Cohort({name: _scores(asked, rows, outcomes, base_rate) for name, rows in values.items()})
        for name in (n for n in values if n not in primary_names(asked)):
            cohort.comparisons.append(self._compare(question, name, values[name], baseline, outcomes, slots.get(name)))
        return cohort

    def _baseline(self, question: str) -> dict[date, ForecastValue]:
        """The primary baseline's values; a part f series under W3's option A has none yet (every pair missing)."""
        if question in INTRADAY_SERIES and SERIES_RATIO_MEASURE == RATIO_INTRADAY:
            return {}
        return primary_values(question_of(question), self.forecasts)

    @staticmethod
    def _started(question: str, values: dict[date, ForecastValue], outcomes: dict[date, Outcome]):
        """A part f series has not started before its first outcome day (resolved or void): earlier forecast days
        are neither unresolved nor missed (W7). A protocol question keeps every day."""
        if question not in INTRADAY_SERIES:
            return values
        start = min(outcomes)
        return {day: v for day, v in values.items() if day >= start}

    def forecasters(self, question: str) -> list[str]:
        return self.forecasts.forecasters(question_of(question))

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
        """A part f series key seeds its own number (after 15) and is never a member's comparison."""
        rows, asked = paired_rows(values, baseline, outcomes), question_of(question)
        return compare(asked, forecaster, " / ".join(sorted(primary_names(asked))), rows, outcomes,
                       seed_word(question, slot, forecaster), miss_start)  # fmt: skip


def _counted(values: dict[date, ForecastValue], after: date | None) -> dict[date, ForecastValue]:
    return values if after is None else {day: v for day, v in values.items() if v.live and day > after}


def _in_cohort(values: dict[date, ForecastValue], live: bool) -> dict[date, ForecastValue]:
    return {day: v for day, v in values.items() if v.live is live}


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
