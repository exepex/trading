"""Criteria 5 and 6: the report scores live forecasts against A16's live RV of the next scored session only (never a
candle outcome), counts void and pending targets, prints the measure label and the gap table."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

import pytest
from v5v1_fixtures import candle_rows, live_rows, oct

from fno.forecast_scoring.v4.outcomes import OutcomeSeries, SeriesOutcomes
from fno.forecast_v4.loss import ranking_qlike
from fno.forecast_v4_rules.records import record
from fno.forecast_v5_v1 import records
from fno.forecast_v5_v1.gap import gap_table
from fno.forecast_v5_v1.report import live_targets, render, score

SESSIONS = [oct(16), oct(19), oct(21), oct(22), oct(23), oct(26)]


def _row(day: date, value: float | None, label="live"):
    status = "ok" if value is not None else "not_eligible"
    g7 = record(day, "v1_rv_next_session", status, value, kind="baseline", slot="reported", label=label,
                method_sha256="a" * 64, inputs_sha256="b" * 64, made_at="")  # fmt: skip
    return records.v5_record(g7, "closes", "p")


def _rows(*pairs):
    return {d.isoformat(): _row(d, v) for d, v in pairs}


def test_the_target_is_the_next_sessions_live_rv():
    live = live_targets(live_rows())
    s = score("f", _rows((oct(19), 1.0e-4), (oct(21), 1.2e-4)), live, SESSIONS)
    assert (s.scored, s.void, s.pending) == (2, 0, 0)
    expected = (ranking_qlike(1.0e-4, 1.142562e-4) + ranking_qlike(1.2e-4, 1.210651e-4)) / 2
    assert s.scores.mean_qlike == pytest.approx(expected, rel=1e-12)


def test_a_void_target_is_counted_and_never_scored():
    s = score("f", _rows((oct(22), 1.0e-4)), live_targets(live_rows()), SESSIONS)  # 23 Oct live is void
    assert (s.scored, s.void, s.scores) == (0, 1, None)


def test_a_void_or_unrecorded_live_target_is_never_resolved_by_a_candle_row():
    # 23 Oct void live; even a candle row for it must not resolve 22 Oct's forecast, and 26 Oct has no live row yet
    live = live_targets(live_rows())
    assert oct(16) in {c.day for c in candle_rows()} and live[oct(16)] is None
    s = score("f", _rows((oct(23), 1.0e-4), (date(2026, 10, 15), 1.0e-4)), live, SESSIONS)
    assert (s.scored, s.pending) == (0, 1)  # 23 Oct -> 26 Oct pending; 15 Oct -> 16 Oct void
    assert s.void == 1


def test_rows_without_a_value_and_backfilled_rows_are_not_scored():
    rows = {oct(19).isoformat(): _row(oct(19), None), oct(21).isoformat(): replace(_row(oct(21), 1e-4), label="x")}
    s = score("f", rows, live_targets(live_rows()), SESSIONS)
    assert (s.rows, s.not_ok, s.scored) == (1, 1, 0)


def test_no_rows_gives_not_enough_data_yet():
    s = score("f", {}, {}, SESSIONS)
    lines = render([s], [])
    assert "| f | 0 | 0 | 0 | 0 | 0 | not enough data yet |" in lines
    assert "Input: candle RV (15m bars) vs live quote RV" in lines


@dataclass(frozen=True)
class Pair:  # the fields of G7b's pairing (amendment 1); the real pairing joins with criterion 5's import test
    day: date
    live: float
    candle: float

    @property
    def ratio(self) -> float:
        return self.candle / self.live


def test_the_gap_table_prints_19_21_and_22_oct():
    live = {r.day: r.value for r in live_rows() if r.value is not None}
    pairs = [Pair(c.day, live[c.day], c.value) for c in candle_rows() if c.day in live and c.value is not None]
    lines = gap_table(pairs)
    assert lines[0] == "Measure gap: candle RV (15m bars) vs live quote RV"
    assert [line.split(" | ")[-1].rstrip(" |") for line in lines[3:]] == ["0.962", "0.997", "1.009"]


def test_no_pairs_says_so():
    assert gap_table([])[1] == "no session has both an ok candle row and an ok live row yet"


class _LiveOnly(OutcomeSeries):
    """v4's own V1 outcome rule (G8, `outcomes.py`) on the same live rows, to check the report's target against it."""

    def __init__(self, live):
        self.live = live

    def sessions(self):
        return [(d, 1.0, 1.0) for d in SESSIONS]

    def close_proxy_rv(self):
        return {}

    def big_move_outcomes(self, question):
        return {}

    def vix_up_outcomes(self):
        return {}

    def intraday_rv(self):
        return self.live


def test_the_target_agrees_with_v4s_own_v1_outcomes():
    live = live_targets(live_rows())
    v4 = SeriesOutcomes(_LiveOnly(live)).outcomes("v1_rv_next_session")
    for d in SESSIONS[:-1]:
        s = score("f", _rows((d, 1.0e-4)), live, SESSIONS)
        if d not in v4:
            assert s.pending == 1, d
        elif v4[d].void:
            assert s.void == 1, d
        else:
            assert s.scores.mean_qlike == pytest.approx(ranking_qlike(1.0e-4, v4[d].value), rel=1e-12), d
