"""Fakes for story FL1-1: G13b's reader port, the official closes, the write-once records and the channel poster."""

from __future__ import annotations

from datetime import date, datetime, time

from fno.cards.posting import CardPoster, PostReceipt
from fno.forecast_lab.lab_close import ReportRecords
from fno.forecast_lab.ranges import STATUS_OK, Outcomes, RangeForecasts, RangeRow, RangeScore, SealedRanges
from fno.models import IST
from tests.checks.builders import CALENDAR

DAY = date(2026, 10, 23)  # Friday, a session
N1_ISSUE, N3_ISSUE = CALENDAR.previous_session(DAY), date(2026, 10, 19)  # 22 Oct; 19 Oct (20 Oct is a holiday)
QUANTILES = {0.05: 25000.0, 0.25: 25200.0, 0.50: 25300.0, 0.75: 25400.0, 0.95: 25600.0}


def at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), IST)


def issue(day: date, sealed_at: datetime | None, underlying="NIFTY", rows=None) -> SealedRanges:
    rows = rows or (RangeRow("rv20", "N1", CALENDAR.next_session(day), QUANTILES, 0.55, STATUS_OK),
                    RangeRow("rv20", "N3", DAY, QUANTILES, 0.55, STATUS_OK))  # fmt: skip
    return SealedRanges(underlying, day, "1545", 25250.0, sealed_at, tuple(rows))


def score(issue_day: date, horizon: str, qs=12.5, inside=(True, True), forecaster="rv20") -> RangeScore:
    return RangeScore(forecaster, horizon, "1545", issue_day, DAY, 25350.0, qs, *inside, 0.2)


class Forecasts(RangeForecasts):
    def __init__(self, issues=(), scores=(), days=()):
        self.issues = {(i.underlying, i.day): i for i in issues}
        self.score_rows, self.days = list(scores), list(days)

    def sealed(self, underlying, day, issue):
        return self.issues.get((underlying, day))

    def scores(self, underlying, target_day):
        return [s for s in self.score_rows if underlying == "NIFTY" and s.target_day == target_day]

    def scored_days(self, underlying, through):
        return [d for d in self.days if d <= through]

    def history(self, underlying, through):
        return [s for s in self.score_rows if underlying == "NIFTY" and s.target_day <= through]


class Closes(Outcomes):
    def __init__(self, archived=True):
        self.archived = archived

    def close(self, underlying, day):
        return 25350.0 if self.archived else None


class Records(ReportRecords):
    def __init__(self):
        self.reports, self.marks = {}, {}

    def report(self, day):
        return self.reports.get(day)

    def write_report(self, day, text, alerts):
        assert day not in self.reports, "write-once"
        self.reports[day] = (text, list(alerts))

    def posted(self, day):
        return day in self.marks

    def mark_posted(self, day, outcome):
        self.marks[day] = outcome


class Poster(CardPoster):
    def __init__(self, *receipts: PostReceipt):
        self.receipts, self.posts = list(receipts), []

    def post(self, text):
        self.posts.append(text)
        return self.receipts.pop(0) if self.receipts else PostReceipt("alert sent", "1700000000.0001", "C")
