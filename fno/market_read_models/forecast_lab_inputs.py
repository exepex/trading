"""What the Forecast lab publishes (story P2b, screen W3b), read from the committed records only, never examples:

- G4's latest daily score report dated on or before the session (`research/forecasts/scores/<day>.json`): the scores,
  the comparisons, the coverage, the AI days G5's gate held back and the AI books' isolation;
- protocol v2's live records (`research/forecasts/live_v2/<YYYY>/<day>_forecasts.csv`: Book 1 and the baselines) and
  the AI books' records (`research/forecasts/ai_v1/<YYYY>/<day>_<book>_forecasts.csv`), each as G3 and F1 wrote it: what
  each forecaster said on the session, and on which days since the common start its records were generated late.

Nothing here scores, re-verifies or recomputes a forecast: G4's report is the scorer's answer, used as is."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from ..forecast.record_files import read_records_v2
from ..forecast.schema_v2 import ForecastRecordV2
from ..research_data.calendar import SessionCalendar
from .forecast_history_inputs import ScoreReportsReader

RECORDS_GLOB = "*/*_forecasts.csv"


@dataclass(frozen=True)
class ForecastLabInputs:
    day: date
    report: dict | None  # G4's latest report on or before the day; None before G4 wrote one
    today: list[ForecastRecordV2]  # every live and AI record made on the day (Book 1, the baselines, the AI books)
    late_days: dict[str, set[date]] = field(default_factory=dict)  # forecaster -> days its records were all late
    record_days: dict[str, set[date]] = field(default_factory=dict)  # forecaster -> days it has records, up to day
    answer_on: Callable[[date, int], date] | None = None  # (session, sessions ahead) -> the session the answer is known


class ForecastLabReader:
    def __init__(self, scores: ScoreReportsReader, record_folders: list[Path], answer_on: Callable[[date, int], date]):
        self.scores, self.record_folders, self.answer_on = scores, [Path(f) for f in record_folders], answer_on

    def on(self, day: date) -> ForecastLabInputs:
        reports = self.scores.on(day)
        records = [r for r in self._records() if r.record.date <= day]
        by_day: dict[tuple[str, date], list[ForecastRecordV2]] = {}
        for r in records:
            by_day.setdefault((r.record.book, r.record.date), []).append(r)
        late, seen = {}, {}
        for (book, d), rows in by_day.items():
            seen.setdefault(book, set()).add(d)
            if not any(r.on_time for r in rows):
                late.setdefault(book, set()).add(d)
        today = [r for r in records if r.record.date == day]
        return ForecastLabInputs(day, reports[-1] if reports else None, today, late, seen, self.answer_on)

    def _records(self) -> list[ForecastRecordV2]:
        files = sorted(p for folder in self.record_folders if folder.is_dir() for p in folder.glob(RECORDS_GLOB))
        return [r for path in files for r in read_records_v2(path.read_text(encoding="utf-8"))]


class SessionsAhead:
    """The session `n` NSE sessions after a day (calendar A7); a day the calendar cannot answer stops the build."""

    def __init__(self, calendar: SessionCalendar):
        self.calendar = calendar

    def __call__(self, day: date, sessions: int) -> date:
        for _ in range(sessions):
            day = self.calendar.next_session(day)
        return day
