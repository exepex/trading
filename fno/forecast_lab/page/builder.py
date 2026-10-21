"""The page's data from live sources (story FL1-1c): today's sealed issue (FL1's `RangeSource`), every scored
forecast with its band (`HistorySource`), the reasons' facts (`FactsSource`) and the regular sessions. It decides
every number the page shows, so the renderers only draw. The method shown is the one with the lowest mean error on
next-session forecasts over its whole record (back-fill and live). Today's issue is shown once written: its seal
(GitHub's push time) can show later and is judged by the seal checks, not here. A missing issue or stale scores is a
system problem: the message says so in one line."""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import replace
from datetime import date, datetime

from ..constants import CALIBRATION_DAYS, ISSUE_CLOSE, UNDERLYINGS
from ..ranges import RangeSource, SealedIssue
from ..sessions import RegularSessions
from .drift import method_problems, stale
from .facts import FactsSource
from .history import HistorySource, ScorePoint, method_record
from .model import Band, Horizon, IndexView, Outcome, PageView, Problem, RangeView, Timeline
from .plain import LIGHT_WORDS, light, when
from .reasons import recent_misses

LIVE = "Live, sealed"
SHOWN, HORIZONS = 30, ("N1", "N3")
DEFAULT_METHOD = "implied"  # with no scored history yet (owner, 21 Oct 2026: the best-proven method, implied)
NO_ISSUE = "{underlying}: today's forecast is missing (none written by {now:%H:%M})"


def _band(row) -> Band:
    q = row.quantiles
    return Band(q[0.05], q[0.25], q[0.50], q[0.75], q[0.95])


def _mean_error(points: list[ScorePoint]) -> float:
    return statistics.fmean(p.error_points for p in points) if points else float("inf")


class PageBuilder:
    def __init__(self, ranges: RangeSource, history: HistorySource, facts: FactsSource, sessions: RegularSessions,
                 underlyings: tuple[str, ...] = UNDERLYINGS):  # fmt: skip
        self.ranges, self.history, self.facts, self.sessions = ranges, history, facts, sessions
        self.underlyings = underlyings

    def build(self, day: date, now: datetime, alerts: tuple[str, ...] = (), checks: tuple[str, ...] = ()) -> PageView:
        facts, drift, system, indices = self.facts.facts(day), [], [], []
        for underlying in self.underlyings:
            issue = self.ranges.sealed(underlying, day, ISSUE_CLOSE)
            if issue is None:  # its seal (GitHub's push time) may show later; the seal checks judge it, not this page
                system.append(NO_ISSUE.format(underlying=underlying, now=now))
            index, problems = self._index(underlying, day, issue, facts)
            indices.append(index)
            drift += [p for p in problems if p.method != "data"]
            system += [f"{p.group}: {p.text}" for p in problems if p.method == "data"]
        return PageView(day, LIVE, tuple(indices), tuple(drift), tuple(system), checks, alerts)

    def _index(self, underlying: str, day: date, issue: SealedIssue | None, facts) -> tuple[IndexView, list[Problem]]:
        by = defaultdict(list)
        for point in self.history.points(underlying):
            if point.target_day < day:
                by[(point.method, point.horizon)].append(point)
        banded = sorted({m for (m, h), ps in by.items() if h == "N1" and any(p.band for p in ps)})
        best = min(banded, key=lambda m: _mean_error(by[(m, "N1")]), default=DEFAULT_METHOD)
        horizons, problems = [], []
        for horizon in HORIZONS:
            days = sorted({p.target_day for (m, h), ps in by.items() if h == horizon for p in ps})
            records = tuple(method_record(by[(m, horizon)], days, days[-SHOWN:], m == best)
                            for m in sorted({m for (m, h) in by if h == horizon}))  # fmt: skip
            problems += [p for r in records for p in method_problems(underlying, horizon, r, days[-20:])]
            row = issue.row(best, horizon) if issue else None
            points = tuple(Outcome(p.target_day, p.close, p.band, bool(p.inside_50), bool(p.inside_90), p.live)
                           for p in by[(best, horizon)] if p.band is not None)  # fmt: skip
            horizons.append(Horizon(Timeline(horizon, best, points, row.target_day if row else None,
                                             _band(row) if row else None), records))  # fmt: skip
        n1 = horizons[0].timeline.points
        problems += stale(underlying, n1[-1].day if n1 else None, self.sessions.previous(day))
        today = tuple(RangeView(r.horizon, r.target_day, _band(r), r.p_up, when(r.horizon, r.target_day, day))
                      for r in (issue.rows if issue else ()) if r.forecaster == best and r.status == "ok")  # fmt: skip
        price = issue.s_ref if issue else (n1[-1].close if n1 else 0.0)
        last = n1[-SHOWN:]
        index = IndexView(underlying, price, "3 pm price" if issue else "last close", best, today, False,
                          sum(p.live for p in n1), CALIBRATION_DAYS, tuple(horizons), sum(p.inside_90 for p in last),
                          len(last), recent_misses(n1, self.sessions.previous, facts))  # fmt: skip
        state = light(index)
        wrong = tuple(p.day for p in reversed(last) if not p.inside_90)
        return replace(index, light=state, light_word=LIGHT_WORDS[state], wrong_days=wrong,
                       backtested=sum(not p.live for p in last)), problems  # fmt: skip
