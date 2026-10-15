"""The card's forecast section (story T1 v1): the latest committed live G1 capture on or before the card's day, every
forecaster and question in it, each with its scored track record (`TrackRecords`). No house-forecast rule is frozen yet
(design 07 section 7.4) and no forecaster has passed a comparison, so all are shown and the card says none is advice.
Protocol v4's forecasters (G6) plug in later as another `ForecastSource`."""

from __future__ import annotations

import json
import re
from datetime import date

from ..constants import FORECAST_QUESTIONS
from ..forecast.record_files import read_records_v2
from ..forecast.schema_v2 import GENERATION_DEADLINE, ForecastRecordV2
from ..models import IST
from .committed import CommittedRecords
from .sections import CardSection, ForecastSource, UsedRecord
from .track_record import TrackRecords

LIVE_FOLDER = "research/forecasts/live_v2"  # G3's live capture, `<YYYY>/<d>_forecasts.csv`
SCORES_FOLDER = "research/forecasts/scores"  # G4's reports, `<d>.json`
CAPTURE_FILE = re.compile(r"(\d{4}-\d{2}-\d{2})_forecasts\.csv")
REPORT_FILE = re.compile(r"(\d{4}-\d{2}-\d{2})\.json")
QUESTION_NAMES = dict(zip(FORECAST_QUESTIONS, (
    "NIFTY higher in 20 sessions", "NIFTY moves 3% or more in 20 sessions",
    "20-day realised volatility rises above the last 20 days'", "India VIX higher in 10 sessions",
    "20-day realised volatility below today's 30-day implied volatility",
)))  # fmt: skip
NONE_YET = "Forecasts: none on record yet"
HEADER = "Forecasts on record: live capture of {day}{age}; track records from the score report of {report}"
OLDER = " (not today's: the latest committed capture)"
LATE = "Generated {at} IST, after the {deadline:%H:%M} deadline: these records are not scored (protocol v2 section 5)"
NOT_ADVICE = "No forecaster has passed a comparison and no house-forecast rule is frozen (design 7.4): none is advice."
FORECASTER_LINE = "  {forecaster} {probability:.2f} | {record}"
NO_FORECAST = "  {forecaster}: no forecast"


def _latest(names: list[str], pattern: re.Pattern, day: date) -> date | None:
    days = [date.fromisoformat(m.group(1)) for m in map(pattern.fullmatch, names) if m]
    return max((d for d in days if d <= day), default=None)


class LiveCaptureForecasts(ForecastSource):
    def __init__(self, records: CommittedRecords, live_folder: str = LIVE_FOLDER, scores_folder: str = SCORES_FOLDER):
        self.records, self.live_folder, self.scores_folder = records, live_folder, scores_folder

    def forecasts(self, day: date) -> CardSection:
        capture = self._latest_capture(day)
        if capture is None:
            return CardSection("forecasts", (NONE_YET,), missing=(f"live forecast capture on or before {day}",))
        path, data = capture
        rows = read_records_v2(data.decode("utf-8"))
        report_day, report = self._latest_report(day)
        used, missing = [UsedRecord.of(path, data)], []
        if report is None:
            missing.append(f"forecast score report on or before {day}")
        else:
            used.append(UsedRecord.of(f"{self.scores_folder}/{report_day}.json", report))
        records = TrackRecords(json.loads(report) if report is not None else None)
        capture_day = rows[0].record.date if rows else day
        lines = [HEADER.format(day=capture_day, age=OLDER if capture_day < day else "", report=report_day or "none")]
        lines += _late_lines(rows) + [NOT_ADVICE] + _question_lines(rows, records)
        return CardSection("forecasts", tuple(lines), tuple(used), tuple(missing))

    def _latest_capture(self, day: date) -> tuple[str, bytes] | None:
        years = sorted(
            (y for y in self.records.names(self.live_folder) if y.isdigit() and int(y) <= day.year), reverse=True
        )
        for year in years:
            found = _latest(self.records.names(f"{self.live_folder}/{year}"), CAPTURE_FILE, day)
            if found is not None:
                path = f"{self.live_folder}/{year}/{found.isoformat()}_forecasts.csv"
                return path, self.records.read(path)
        return None

    def _latest_report(self, day: date) -> tuple[str | None, bytes | None]:
        found = _latest(self.records.names(self.scores_folder), REPORT_FILE, day)
        if found is None:
            return None, None
        return found.isoformat(), self.records.read(f"{self.scores_folder}/{found.isoformat()}.json")


def _late_lines(rows: list[ForecastRecordV2]) -> list[str]:
    late = sorted({r.generated_at.astimezone(IST).strftime("%H:%M") for r in rows if not r.on_time})
    return [LATE.format(at=", ".join(late), deadline=GENERATION_DEADLINE)] if late else []


def _question_lines(rows: list[ForecastRecordV2], records: TrackRecords) -> list[str]:
    lines = []
    for question in FORECAST_QUESTIONS:
        asked = [r.record for r in rows if r.record.question == question]
        if not asked:
            continue
        lines.append(f"{question} ({QUESTION_NAMES[question]}):")
        for r in asked:
            if r.probability is None:
                lines.append(NO_FORECAST.format(forecaster=r.book))
            else:
                record = records.line(r.book, question, r.probability)
                lines.append(FORECASTER_LINE.format(forecaster=r.book, probability=r.probability, record=record))
    return lines
