"""A22d, criteria D1-D3: Groww's lone flat 09:15 candle, read live from 09:10 to before 09:15, is the pre-open value;
every other shape keeps A22's incomplete outcome; the 09:09 candle always wins."""

from __future__ import annotations

import json
from datetime import time

import pytest

from fno.preopen.answers import read_index_preopen

from .fixtures import DAY, candles, flat_0915, ist

NOT_A_VALUE = ("no pre-open value: candles only from 09:15", "no 09:09 candle yet")


@pytest.mark.parametrize("seen", [ist(9, 10), ist(9, 10, 59), ist(9, 14, 59)])
def test_d1_the_lone_flat_0915_candle_read_before_0915_is_the_value(seen):
    reading = read_index_preopen(flat_0915(close=7777.25), DAY, "nifty", seen)
    assert reading.complete and reading.detail == ""
    assert reading.values == {"nifty_preopen": "7777.25", "nifty_preopen_basis": "flat_0915"}
    assert reading.source_time is None  # its 09:15 stamp is later than the read, not the value's time


@pytest.mark.parametrize("volume", [None, 0, 0.0])
def test_d1_no_volume_is_null_or_zero(volume):
    assert read_index_preopen(flat_0915(volume=volume), DAY, "banknifty", ist(9, 10)).complete


def test_d1_a_row_without_a_volume_field_counts_as_no_volume():
    stamp = f"{DAY}T09:15:00"
    data = json.dumps({"candles": [[stamp, 1.5, 1.5, 1.5, 1.5]]}).encode()
    assert read_index_preopen(data, DAY, "nifty", ist(9, 10)).values["nifty_preopen"] == "1.5"


def _two(first: list, second: list) -> bytes:
    return json.dumps({"candles": [first, second]}).encode()


def _row(at: time, o: float, h: float, low: float, c: float, volume=None) -> list:
    return [f"{DAY}T{at.isoformat()}", o, h, low, c, volume]


@pytest.mark.parametrize(
    ("data", "seen"),
    [
        (flat_0915(), ist(9, 15)),  # boundary: from 09:15 the candle may be a traded minute
        (flat_0915(), ist(9, 16)),
        (flat_0915(), ist(9, 9, 59)),  # boundary: before the pre-open result is final
        (flat_0915(), ist(9, 12, day=DAY.replace(day=21))),  # read on another day
        (json.dumps({"candles": [_row(time(9, 15), 1.0, 2.0, 1.0, 1.5)]}).encode(), ist(9, 10)),  # not flat
        (json.dumps({"candles": [_row(time(9, 15), 1.0, 1.0, 1.0, 1.0)[:5] + [1]]}).encode(), ist(9, 10)),  # volume
        (_two(_row(time(9, 5), 1.0, 1.0, 1.0, 1.0), _row(time(9, 15), 1.0, 1.0, 1.0, 1.0)), ist(9, 10)),  # beside
        (_two(_row(time(9, 15), 1.0, 1.0, 1.0, 1.0), _row(time(9, 16), 1.0, 1.0, 1.0, 1.0)), ist(9, 10)),  # two
        (flat_0915(stamp=time(9, 14)), ist(9, 10)),  # stamped 09:14
        (flat_0915(stamp=time(9, 16)), ist(9, 10)),  # stamped 09:16
        (flat_0915(day=DAY.replace(day=21)), ist(9, 10)),  # another day's candle
        (candles(count=0), ist(9, 10)),  # an empty list
    ],
)
def test_d2_every_other_shape_is_not_a_value(data, seen):
    reading = read_index_preopen(data, DAY, "nifty", seen)
    assert not reading.complete and reading.values == {} and reading.detail in NOT_A_VALUE


@pytest.mark.parametrize("volume", ["0", True, 2.5])
def test_d2_a_volume_that_is_not_a_zero_number_is_not_no_volume(volume):
    assert not read_index_preopen(flat_0915(volume=volume), DAY, "nifty", ist(9, 10)).complete


def test_d2_a_flat_candle_read_from_0915_keeps_a22s_line():
    reading = read_index_preopen(flat_0915(), DAY, "nifty", ist(9, 15))
    assert reading.detail == "no pre-open value: candles only from 09:15"


def test_d3_the_0909_candle_wins_over_a_flat_0915_candle():
    rows = json.loads(candles())["candles"] + [_row(time(9, 15), 8888.0, 8888.0, 8888.0, 8888.0)]
    reading = read_index_preopen(json.dumps({"candles": rows}).encode(), DAY, "nifty", ist(9, 10))
    assert reading.values == {"nifty_preopen": "5555.5", "nifty_preopen_basis": "candle_0909"}
    assert reading.source_time == ist(9, 10)


def test_d1_a_utc_seen_at_is_read_in_ist():
    from datetime import UTC

    seen = ist(9, 10).astimezone(UTC)  # Groww's `received_at` may come in UTC: 03:40 UTC is 09:10 IST
    assert read_index_preopen(flat_0915(), DAY, "nifty", seen).complete
    assert not read_index_preopen(flat_0915(), DAY, "nifty", ist(9, 15).astimezone(UTC)).complete
