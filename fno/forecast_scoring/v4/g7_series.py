"""The adapter from G7's series rules (`fno/forecast_v4_rules/series.py`, story G7) to G8's `OutcomeSeries`: G8
re-implements none of them (regular-session filter, close-proxy RV_s, the V6 outcomes, A16's live rows)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from ...forecast_v4.terms import HORIZON_SESSIONS
from ...forecast_v4_rules import series
from .outcomes import OutcomeSeries


class G7Series(OutcomeSeries):
    def __init__(self, closes_text: str, a16_rows: Callable[[], list[dict]]):
        """`closes_text`: `warmup_closes.csv`; `a16_rows`: A16's live `rv/` rows (read only when V1 asks)."""
        self.rows, self.a16_rows = series.closes_rows(closes_text), a16_rows
        self.closes = series.regular_closes(self.rows)

    def sessions(self) -> list[tuple[date, float, float]]:
        vix = {v.day: v.value for v in series.vix_closes(self.rows)}
        return [(c.day, c.value, vix[c.day]) for c in self.closes]

    def close_proxy_rv(self) -> dict[date, float]:
        return {v.day: v.value for v in series.close_proxy_rv(self.closes)}

    def big_move_outcomes(self, question: str) -> dict[date, bool]:
        return {o.day: o.value for o in series.big_move_outcomes(self.closes, HORIZON_SESSIONS[question])}

    def intraday_rv(self) -> dict[date, float | None]:
        return {s.day: s.value for s in series.live_intraday_rv(self.a16_rows())}
