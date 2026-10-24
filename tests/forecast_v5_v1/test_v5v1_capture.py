"""Criteria 3 and 4: each G14 value equals G7's own function on the same series (G7's public functions, no copy);
every row carries the input measure, its sources and G14's method hash; v4's capture refusals hold."""

from __future__ import annotations

from datetime import timedelta
from functools import cache
from pathlib import Path

import pytest
from v5v1_fixtures import candle_rows, oct

from fno.config import ROOT
from fno.forecast_v4_rules.baselines import Ewma, Har, trailing_previous_session
from fno.forecast_v4_rules.capture import CaptureRefused, cutoff
from fno.forecast_v4_rules.rules import close_blend
from fno.forecast_v4_rules.series import DayValue, close_proxy_rv
from fno.forecast_v4_rules.wiring import build_v4_forecasts
from fno.forecast_v5_v1 import records
from fno.forecast_v5_v1.capture import V5Day, capture
from fno.forecast_v5_v1.method import method_sha256

D = oct(22)
MADE_ON = "python 3; numpy 2; libc glibc 2.39"


@cache
def _inputs():
    return build_v4_forecasts(D).inputs


def _day(d=D) -> V5Day:
    return V5Day(_inputs(), candle_rows(), d, method_sha256(ROOT))


def _captured(tmp_path: Path, now) -> dict[str, records.V5Record]:
    capture(_day(), now, MADE_ON, lambda f, q, rows: records.write(tmp_path, f, q, rows))
    files = sorted(tmp_path.glob("*/*.csv"))
    return {file.parent.name: records.read(file)[D.isoformat()] for file in files}


def test_each_value_equals_g7s_own_function_on_the_same_series(tmp_path):
    rows = _captured(tmp_path, cutoff(D) - timedelta(minutes=18))
    inputs, day = _inputs(), _day()
    spliced = [DayValue(s.rv.day, s.rv.value) for s in day.spliced]
    rv = close_proxy_rv(inputs.closes)
    ewma, har = Ewma(rv).forecast(D, 1), Har(rv, 1, inputs.sessions).forecast(D)
    expected = {
        "v5c_trailing": trailing_previous_session([s.rv for s in day.spliced], oct(21)),
        "v5c_ewma_094": ewma,
        "v5c_har_daily": har,
        "v5c_har_intraday": Har(spliced, 1, inputs.sessions, minimum=1).forecast(D),
        "v5c_close_blend": close_blend(har, ewma),
    }
    assert {name: float(row.value) for name, row in rows.items()} == {n: v.value for n, v in expected.items()}
    assert {row.status for row in rows.values()} == {"ok"}


def test_har_intraday_reads_the_candle_history_and_the_others_do_not(tmp_path):
    rows = _captured(tmp_path, cutoff(D) - timedelta(minutes=18))
    candle = sum(s.source == "candle" for s in _day().spliced)
    assert candle > 1600
    assert rows["v5c_har_intraday"].input_sources == f"candle:{candle};live:1"
    assert rows["v5c_trailing"].input_sources == "candle:0;live:1"
    assert {rows[n].input_sources for n in ("v5c_ewma_094", "v5c_har_daily", "v5c_close_blend")} == {"closes"}


def test_every_row_carries_the_measure_label_the_method_hash_and_the_platform(tmp_path):
    rows = _captured(tmp_path, cutoff(D) - timedelta(minutes=18))
    assert len(rows) == 5
    for row in rows.values():
        assert row.input_measure == "candle RV (15m bars) vs live quote RV"
        assert row.method_sha256 == method_sha256(ROOT)
        assert row.platform == MADE_ON
        assert row.label == "live"


def test_without_the_candle_history_v1_has_not_started():
    values = V5Day(_inputs(), [], D, "x").forecasts.values(D)
    assert values[("har_intraday", "v1_rv_next_session")].status == "not_started"  # 3 usable live rows, v4's gate is 20


def test_at_the_cutoff_nothing_is_written(tmp_path):
    with pytest.raises(CaptureRefused):
        _captured(tmp_path, cutoff(D))
    assert list(tmp_path.glob("*/*.csv")) == []


def test_a_row_is_made_on_its_own_day_only(tmp_path):
    with pytest.raises(CaptureRefused):
        _captured(tmp_path, cutoff(D) + timedelta(days=1) - timedelta(hours=2))


def test_a_second_capture_the_same_day_adds_nothing(tmp_path):
    now = cutoff(D) - timedelta(minutes=18)
    write = lambda f, q, rows: records.write(tmp_path, f, q, rows)  # noqa: E731
    assert capture(_day(), now, MADE_ON, write) == 5
    assert capture(_day(), now + timedelta(minutes=1), "another machine", write) == 0


def test_monday_26_oct_trailing_is_missing_with_no_input():
    inputs = build_v4_forecasts(oct(26)).inputs
    day = V5Day(inputs, candle_rows(), oct(26), "x")
    assert day.forecasts.values(oct(26))[("trailing", "v1_rv_next_session")].status == "missing"  # 23 Oct void
    assert day.sources("trailing") == "candle:0;live:0"
