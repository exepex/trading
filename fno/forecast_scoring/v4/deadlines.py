"""The 15:10 deadline in G8 (story G10 completion, criterion 8): a live row whose verdict is `late` is no forecast that
day (a miss under G9's caps); a live row with no verdict yet is counted "deadline not checked", and a confirmatory
look refuses while one exists up to its date (the reconciliation's pattern, response 213). Back-fill rows and the AI
books (their commitment is their sealed submission, G11) are never checked here."""

from __future__ import annotations

from datetime import date

from ...v4_pack.commitments import SEALED_COMMITMENTS
from ...v4_pack.deadline import LATE, parse_verdicts
from .drive_records import DriveRecords
from .inputs import ForecastValue, V4ForecastSource
from .reconcile import LookBlocked

UNCHECKED = (
    "a look on {look} needs every live row's 15:10 deadline checked: {count} day(s) not checked, the earliest {day}"
)


class DeadlineVerdicts:
    def __init__(self, records: DriveRecords):
        self.records, self._by_day = records, None

    def by_day(self) -> dict[date, dict[tuple[str, str], str]]:
        if self._by_day is None:
            self._by_day = dict(parse_verdicts(data) for data in self.records.files().values())
        return self._by_day


class LateCommitmentsOut(V4ForecastSource):
    def __init__(self, forecasts: V4ForecastSource, verdicts: DeadlineVerdicts):
        self.forecast_source, self.verdicts = forecasts, verdicts
        self.unchecked: set[date] = set()  # live days read so far whose row has no verdict

    def forecasters(self, question: str) -> list[str]:
        return self.forecast_source.forecasters(question)

    def values(self, question: str, forecaster: str) -> dict[date, ForecastValue]:
        values = self.forecast_source.values(question, forecaster)
        if forecaster in SEALED_COMMITMENTS:
            return values
        return {day: self._checked(day, value, (forecaster, question)) for day, value in values.items()}

    def _checked(self, day: date, value: ForecastValue, key: tuple[str, str]) -> ForecastValue:
        if not value.live:
            return value
        verdict = self.verdicts.by_day().get(day, {}).get(key)
        if verdict is None:
            self.unchecked.add(day)
            return value
        return ForecastValue(None, True) if verdict == LATE else value


def unchecked_days(source: LateCommitmentsOut, questions: tuple[str, ...]) -> list[date]:
    """Every live day, over all questions and forecasters, whose row has no deadline verdict."""
    for question in questions:
        for forecaster in source.forecasters(question):
            source.values(question, forecaster)
    return sorted(source.unchecked)


def require_checked(unchecked: list[date], look_day: date) -> None:
    due = [day for day in unchecked if day <= look_day]
    if due:
        raise LookBlocked(UNCHECKED.format(look=look_day, count=len(due), day=due[0]))
