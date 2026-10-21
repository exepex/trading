"""Fakes for story FL1-1: G13b's reader port, the official closes, the write-once records and the channel poster."""

from __future__ import annotations

from datetime import date, datetime, time
from functools import partial

from fno.forecast_lab.delivery import Attachment, Delivery, ReportPoster
from fno.forecast_lab.lab_close import LabClose, ReportRecords
from fno.forecast_lab.match import MatchSection
from fno.forecast_lab.ranges import STATUS_OK, Outcomes, RangeRow, RangeScore, RangeSource, SealedIssue
from fno.forecast_lab.report import CloseReport
from fno.forecast_lab.sessions import RegularSessions
from fno.models import IST
from tests.checks.builders import CALENDAR
from tests.desk.conftest import RecordingAlerts

SESSIONS = RegularSessions(CALENDAR)  # NSE's real calendar: 20 Oct 2026 is a holiday, 8 Nov a muhurat session
DAY = date(2026, 10, 23)  # Friday: the targets matched
REPORT_DAY = SESSIONS.next(DAY)  # Monday 26 Oct: its report matches 23 Oct's targets
N1_ISSUE, N3_ISSUE = SESSIONS.previous(DAY), date(2026, 10, 19)  # 22 Oct; 19 Oct (20 Oct is a holiday)
G13B_LIVE = date(2026, 10, 1)  # G13b's first live day in these tests: every issue below is expected
QUANTILES = {0.05: 25000.0, 0.25: 25200.0, 0.50: 25300.0, 0.75: 25400.0, 0.95: 25600.0}


def at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), IST)


def issue(day: date, sealed_at: datetime | None = None, underlying="NIFTY", rows=None) -> SealedIssue:
    """An issue sealed at 15:50 on its own day unless told otherwise."""
    n3 = SESSIONS.next(SESSIONS.next(SESSIONS.next(day)))
    rows = rows or (RangeRow("rv20", "N1", SESSIONS.next(day), QUANTILES, 0.55, STATUS_OK),
                    RangeRow("rv20", "N3", n3, QUANTILES, 0.55, STATUS_OK))  # fmt: skip
    return SealedIssue(underlying, day, "1545", 25250.0, sealed_at or at(day, 15, 50), tuple(rows))


def score(issue_day: date, horizon: str, qs=12.5, inside=(True, True), forecaster="rv20", target=DAY) -> RangeScore:
    return RangeScore(forecaster, horizon, "1545", issue_day, target, 25350.0, qs, *inside, 0.2)


def scored(*targets: date) -> tuple[RangeScore, ...]:
    """G13b's score of every row `issue` writes (rv20 at N1 and N3) aimed at `targets`."""
    return tuple(score(SESSIONS.back(t, n), h, target=t) for t in targets for h, n in (("N1", 1), ("N3", 3)))


def on_time(*targets: date) -> tuple[SealedIssue, ...]:
    """Every N1 and N3 issue aimed at `targets`, sealed on time."""
    days = {SESSIONS.back(t, n) for t in targets for n in (1, 3)}
    return tuple(issue(d) for d in sorted(days))


class Forecasts(RangeSource):
    def __init__(self, issues=(), scores=(), days=None):
        """`days`: the scored target days, by underlying."""
        self.issues = {(i.underlying, i.day): i for i in issues}
        self.score_rows, self.days = list(scores), days or {}

    def sealed(self, underlying, day, issue):
        return self.issues.get((underlying, day))

    def scores(self, underlying, target_day):
        return [s for s in self.score_rows if underlying == "NIFTY" and s.target_day == target_day]

    def scored_days(self, underlying, through):
        return [d for d in self.days.get(underlying, []) if d <= through]

    def history(self, underlying, through):
        return [s for s in self.score_rows if underlying == "NIFTY" and s.target_day <= through]


class Closes(Outcomes):
    def __init__(self, archived=(DAY,)):
        self.archived = set(archived)

    def close(self, underlying, day):
        return 25350.0 if day in self.archived else None


class Records(ReportRecords):
    def __init__(self):
        self.reports, self.marks, self.alert_marks = {}, {}, {}

    def report(self, day):
        return self.reports.get(day)

    def write_report(self, day, report):
        assert day not in self.reports, "write-once"
        self.reports[day] = report

    def posted(self, day):
        return day in self.marks

    def mark_posted(self, day, outcome):
        self.marks[day] = outcome

    def alerted(self, day):
        return day in self.alert_marks

    def mark_alerted(self, day, outcomes):
        assert day not in self.alert_marks, "write-once"
        self.alert_marks[day] = list(outcomes)


class Poster(ReportPoster):
    def __init__(self, *deliveries: Delivery):
        self.deliveries, self.posts, self.files = list(deliveries), [], []

    def post(self, text, attachments):
        self.posts.append(text)
        self.files.append([a.name for a in attachments])
        return self.deliveries.pop(0) if self.deliveries else Delivery("posted to #fno-forecast", sent=True)


class EchoMaker:
    """The message as FL1-1's seal-check and match lines, with one file: so the coverage tests read what they check."""

    def make(self, day, now, alerts, checks):
        return checks, (Attachment(f"forecast-{day}.html", b"<p>details</p>", "Details"),), ()


def lab(forecasts, records=None, poster=None, alerts=None, closes=None, first_day=DAY, underlyings=("NIFTY",),
        today=REPORT_DAY, issues_from=G13B_LIVE):  # fmt: skip
    """The lab with fakes; its window starts at `first_day` (the lab's first live day), G13b live from `issues_from`."""
    match = MatchSection(forecasts, closes or Closes(), SESSIONS, issues_from)
    report = CloseReport(forecasts, match, first_day, underlyings=underlyings)
    records, poster, alerts = records or Records(), poster or Poster(), alerts or RecordingAlerts()
    run = LabClose(report, EchoMaker(), records, poster, alerts, SESSIONS.is_regular, partial(at, today, 15, 47))
    return run, poster, alerts
