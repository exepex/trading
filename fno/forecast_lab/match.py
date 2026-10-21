"""The 15:45 report's forecast sections (story FL1-1): each sealed range whose target is today against today's official
close, with G13b's own scores (never recomputed here), and the next session's sealed ranges. A forecast counts only if
its seal (the receipt's GitHub push time) came before its target day's open; a missing or late one is said and
alerted, never skipped."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime

from ..models import IST
from .constants import HORIZON_SESSIONS, ISSUE_CLOSE, LATE, LEVELS, NO_ISSUE, NOT_ARCHIVED, NOT_SEALED_YET, SEAL_BY
from .ranges import STATUS_OK, Outcomes, RangeRow, RangeScore, RangeSource, SealedIssue


def opens(day: date) -> datetime:
    return datetime.combine(day, SEAL_BY, IST)


def sealed_in_time(issue: SealedIssue, target_day: date) -> bool:
    return not issue.late and issue.sealed_at is not None and issue.sealed_at < opens(target_day)


def band(row: RangeRow) -> str:
    return "/".join(f"{row.quantiles[level]:.0f}" for level in LEVELS)


def _hit(flag: bool | None) -> str:
    return "n/a" if flag is None else ("in" if flag else "out")


def _direction(row: RangeRow, s_ref: float, outcome: float) -> str:
    called, moved = row.quantiles[0.50] - s_ref, outcome - s_ref
    return "right" if called * moved > 0 else "wrong" if called * moved < 0 else "flat"


def score_line(row: RangeRow, score: RangeScore, s_ref: float) -> str:
    return (
        f"  {row.forecaster}: 5/25/50/75/95 {band(row)}; close {score.outcome:.2f}: 25-75 {_hit(score.inside_25_75)}, "
        f"5-95 {_hit(score.inside_05_95)}, median direction {_direction(row, s_ref, score.outcome)}, "
        f"quantile score {score.quantile_score:.2f}"
    )


class MatchSection:
    def __init__(self, forecasts: RangeSource, outcomes: Outcomes, previous_session: Callable[[date], date]):
        self.forecasts, self.outcomes, self.previous = forecasts, outcomes, previous_session

    def issue_day(self, target_day: date, sessions: int) -> date:
        day = target_day
        for _ in range(sessions):
            day = self.previous(day)
        return day

    def lines(self, underlying: str, day: date) -> tuple[list[str], list[str]]:
        """(report lines, alert texts) for today's targets."""
        if self.outcomes.close(underlying, day) is None:
            return [NOT_ARCHIVED.format(underlying=underlying)], []
        out, alerts = [f"{underlying}: today's ranges against the close"], []
        scores = self.forecasts.scores(underlying, day)
        for horizon, sessions in HORIZON_SESSIONS.items():
            issue_day = self.issue_day(day, sessions)
            issue = self.forecasts.sealed(underlying, issue_day, ISSUE_CLOSE)
            what = {"underlying": underlying, "horizon": horizon, "issue_day": issue_day}
            if issue is None:
                alerts.append(NO_ISSUE.format(**what))
                out.append(alerts[-1])
            elif not sealed_in_time(issue, day):
                alerts.append(LATE.format(**what, sealed=issue.sealed_at or "no push evidence"))
                out.append(alerts[-1])
            else:
                out.append(f" {horizon}, issued {issue_day} 15:45 at {issue.s_ref:.2f}:")
                out.extend(self._scored(issue, horizon, issue_day, scores))
        return out, alerts

    @staticmethod
    def _scored(issue: SealedIssue, horizon: str, issue_day: date, scores: list[RangeScore]) -> list[str]:
        lines = []
        for score in sorted(scores, key=lambda s: s.forecaster):
            row = issue.row(score.forecaster, horizon)
            if score.horizon == horizon and score.issue_day == issue_day and row and row.status == STATUS_OK:
                lines.append(score_line(row, score, issue.s_ref))
        return lines or ["  no scored row yet (G13b scores after the close is archived)"]


def next_ranges(underlying: str, issue: SealedIssue | None, now: datetime) -> list[str]:
    """Today's 15:45 issue, shown only once sealed (pushed) by the time the report is built."""
    if issue is None or issue.late or issue.sealed_at is None or issue.sealed_at > now:
        return [NOT_SEALED_YET.format(underlying=underlying)]
    lines = [f"{underlying}: sealed ranges for the next sessions (from {issue.s_ref:.2f})"]
    for row in sorted(issue.rows, key=lambda r: (r.horizon, r.forecaster)):
        if row.status == STATUS_OK:
            up = "" if row.p_up is None else f", P(up) {row.p_up:.2f}"
            lines.append(f"  {row.horizon} ({row.target_day}) {row.forecaster}: 5/25/50/75/95 {band(row)}{up}")
    return lines
