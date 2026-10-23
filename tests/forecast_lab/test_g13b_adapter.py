"""Story FL1-1's adapter over G13b's reader (its shapes as on story/g13b-price-ranges 7c3b0aa3, agreed 21 Oct)."""

from dataclasses import dataclass
from datetime import date

from fno.forecast_lab.g13b_adapter import G13bCloses, G13bRanges

from .builders import DAY, N1_ISSUE, at

ROW = {"forecaster": "rv20", "horizon": "N1", "target_day": "2026-10-23", "status": "ok", "reason": "", "p_up": 0.52,
       "q05": 25000.0, "q25": 25200.0, "q50": 25300.0, "q75": 25400.0, "q95": 25600.0}  # fmt: skip
NOT_ELIGIBLE = {"forecaster": "rv20", "horizon": "N3", "target_day": None, "status": "not_eligible",
                "reason": "the session calendar ends before the target"}  # fmt: skip
SCORE = {"label": "live", "underlying": "NIFTY", "issue": "1545", "issue_day": "2026-10-22", "forecaster": "rv20",
         "horizon": "N1", "target_day": "2026-10-23", "outcome_close": 25350.0, "outcome_log": 0.0,
         "quantile_score": 12.5, "inside_25_75": True, "inside_05_95": True, "brier_up": 0.23}  # fmt: skip


@dataclass
class Found:  # G13b's SealedRanges: record, sealed_at, late
    record: dict
    sealed_at: object
    late: bool


class Forecasts:
    def sealed(self, underlying, day, issue):
        record = {"s_ref": 25250.0, "rows": [ROW, NOT_ELIGIBLE]}
        return Found(record, at(day, 15, 50), False) if day == N1_ISSUE else None


class Scores:
    def rows(self, underlying, live_only=False):
        backfill = {**SCORE, "label": "backfill_eod", "target_day": "2026-10-21"}
        return [SCORE] if live_only else [SCORE, backfill]

    def scored_days(self, underlying, through):
        return [date(2026, 10, 23)]


class Closes:
    def close(self, underlying, day):
        return 25350.0


def test_records_and_scores_map_one_to_one_and_a_not_eligible_row_is_left_out():
    ranges = G13bRanges(Forecasts(), Scores())
    issue = ranges.sealed("NIFTY", N1_ISSUE, "1545")
    (row,) = issue.rows
    assert (issue.s_ref, issue.sealed_at, issue.late) == (25250.0, at(N1_ISSUE, 15, 50), False)
    assert (row.target_day, row.quantiles[0.05], row.quantiles[0.95], row.p_up) == (DAY, 25000.0, 25600.0, 0.52)
    assert ranges.sealed("NIFTY", DAY, "1545") is None
    (score,) = ranges.scores("NIFTY", DAY)
    assert (score.issue_day, score.outcome, score.quantile_score, score.brier_up) == (N1_ISSUE, 25350.0, 12.5, 0.23)
    assert [s.target_day for s in ranges.history("NIFTY", DAY)] == [DAY]  # live only
    assert ranges.scored_days("NIFTY", DAY) == [DAY]
    assert G13bCloses(Closes()).close("NIFTY", DAY) == 25350.0
