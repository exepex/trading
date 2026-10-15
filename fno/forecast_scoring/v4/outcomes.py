"""Each forecast day's v4 outcome (protocol v4 sections 1-2; story G8), formed from G7's series rules
(`fno/forecast_v4_rules/series.py`, the one place for regular sessions, close-proxy RV_s, the V6 outcomes and A16's
live rv rows; agreed 15 Oct 2026) behind `OutcomeSeries`. G8 adds only the horizon sums (V2, V3), V1's next-session
row and V7's `VIX(d+5) > VIX(d)`. A forecast day whose horizon runs past the data has no entry (unresolved)."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from datetime import date

from ...constants import V1_RV_1S, V2_RV_5S, V3_RV_20S, V6_BIG_MOVE_1S, V6_BIG_MOVE_5S, V7_VIX_UP_5S
from ...forecast_v4.terms import HORIZON_SESSIONS
from .inputs import Outcome, V4OutcomeSource

VOID_PLACEHOLDER = 0.0  # pairs.py reads a None outcome as unresolved before void; a void day's value is never used


class OutcomeSeries(ABC):
    @abstractmethod
    def sessions(self) -> list[tuple[date, float, float]]:
        """(day, official close, closing India VIX) of every A7 regular session, in date order."""

    @abstractmethod
    def close_proxy_rv(self) -> dict[date, float]:
        """Each regular session's close-proxy RV_s (from the previous regular close)."""

    @abstractmethod
    def big_move_outcomes(self, question: str) -> dict[date, bool]:
        """V6a or V6b's outcome per forecast day, resolved days only."""

    @abstractmethod
    def intraday_rv(self) -> dict[date, float | None]:
        """A16's live session RV_s per session; None for a void session."""


class SeriesOutcomes(V4OutcomeSource):
    def __init__(self, series: OutcomeSeries):
        self.series = series

    def outcomes(self, question: str) -> dict[date, Outcome]:
        sessions = self.series.sessions()
        index = {s[0]: i for i, s in enumerate(sessions)}
        return {
            day: Outcome(value, void, *_first_session(sessions, index[day]))
            for day, (value, void) in self._values(question, sessions).items()
            if index[day] + 1 < len(sessions)
        }

    def _values(self, question: str, sessions) -> dict[date, tuple[object, bool]]:
        days, horizon = [s[0] for s in sessions], HORIZON_SESSIONS[question]
        found: dict[date, tuple[object, bool]] = {}
        if question in (V6_BIG_MOVE_1S, V6_BIG_MOVE_5S):
            outcomes = self.series.big_move_outcomes(question)
            return {day: (outcomes[day], False) for day in days if day in outcomes}
        rv, intraday, vix = self.series.close_proxy_rv(), self.series.intraday_rv(), [s[2] for s in sessions]
        for i, day in enumerate(days[: len(days) - horizon]):
            ahead = days[i + 1 : i + 1 + horizon]
            if question in (V2_RV_5S, V3_RV_20S):
                found[day] = (sum(rv[t] for t in ahead), False)
            elif question == V7_VIX_UP_5S:
                found[day] = (vix[i + horizon] > vix[i], False)
            elif question == V1_RV_1S and ahead[0] in intraday:
                void = intraday[ahead[0]] is None
                found[day] = (VOID_PLACEHOLDER if void else intraday[ahead[0]], void)
        return found


def _first_session(sessions, i: int) -> tuple[float, float]:
    """The regime inputs: the outcome's first session's closing VIX and its log return."""
    return sessions[i + 1][2], math.log(sessions[i + 1][1] / sessions[i][1])
