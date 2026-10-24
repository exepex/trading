"""Criterion 1: the splice is point in time and candle first, on the real 16-23 Oct 2026 rows."""

from __future__ import annotations

from datetime import date, timedelta

from v5v1_fixtures import candle_rows, live_rows, oct

from fno.forecast_v4_rules.capture import cutoff
from fno.forecast_v4_rules.series import SessionRv
from fno.forecast_v5_v1.history import CANDLE, LIVE, source_counts, splice


def _for(d: date) -> dict[date, tuple[float, str]]:
    return {s.rv.day: (s.rv.value, s.source) for s in splice(candle_rows(), live_rows(), d, cutoff(d))}


def test_16_oct_is_missing_for_19_oct_and_the_candle_value_from_21_oct():
    assert oct(16) not in _for(oct(19))  # live void; candle first seen 19 Oct 15:33 IST, after 19 Oct's 14:30
    assert _for(oct(21))[oct(16)] == (5.82224e-5, CANDLE)
    assert _for(oct(22))[oct(16)] == (5.82224e-5, CANDLE)


def test_a_candle_row_first_seen_after_the_cutoff_is_never_read():
    # 19 Oct's candle row was first seen on 21 Oct at 15:33 IST: for 21 Oct, 19 Oct is the live row
    assert _for(oct(21))[oct(19)] == (1.533569e-4, LIVE)
    assert _for(oct(22))[oct(19)] == (1.476017e-4, CANDLE)


def test_the_previous_session_always_comes_from_the_live_row():
    for d, previous in ((oct(21), oct(19)), (oct(22), oct(21)), (oct(23), oct(22))):
        assert _for(d)[previous][1] == LIVE


def test_a_session_with_neither_an_ok_candle_row_nor_an_ok_live_row_is_missing():
    # 23 Oct: live void, no candle row yet; for Monday 26 Oct it is missing
    assert oct(23) not in _for(oct(26))
    assert oct(22) in _for(oct(26))


def test_the_cutoff_itself_is_too_late():
    d = oct(21)
    at, just_before = cutoff(d), cutoff(d) - timedelta(microseconds=1)
    rows = [SessionRv(oct(19), 2.0, at)]
    assert splice(rows, [], d, cutoff(d)) == []
    assert [s.rv.value for s in splice([SessionRv(oct(19), 2.0, just_before)], [], d, cutoff(d))] == [2.0]


def test_the_day_itself_and_later_days_are_never_read():
    d = oct(21)
    early = cutoff(d) - timedelta(days=3)
    rows = [SessionRv(oct(21), 1.0, early), SessionRv(oct(22), 1.0, early)]
    assert splice(rows, rows, d, cutoff(d)) == []


def test_a_void_candle_row_falls_back_to_the_live_row():
    early = cutoff(oct(21)) - timedelta(days=1)
    spliced = splice([SessionRv(oct(19), None, early)], [SessionRv(oct(19), 3.0, early)], oct(21), cutoff(oct(21)))
    assert [(s.rv.value, s.source) for s in spliced] == [(3.0, LIVE)]


def test_nothing_in_gives_nothing_out():
    assert splice([], [], oct(21), cutoff(oct(21))) == []
    assert source_counts([]) == "candle:0;live:0"


def test_the_source_counts_match_the_inputs():
    spliced = splice(candle_rows(), live_rows(), oct(21), cutoff(oct(21)))
    candle = sum(s.source == CANDLE for s in spliced)
    assert source_counts(spliced) == f"candle:{candle};live:{len(spliced) - candle}"
    assert len(spliced) - candle == 1  # 19 Oct only (16 Oct live is void, 21 Oct is the day)
