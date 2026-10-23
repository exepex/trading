"""Criteria 1-3: the readers of GIFT Nifty, NSE's F&O pre-open list and the 09:09 index candle."""

from __future__ import annotations

from datetime import time

import pytest

from fno.preopen.answers import BadAnswer, read_gift_nifty, read_index_preopen, read_preopen_list

from .fixtures import DAY, candles, fo_list, gift, ist


def test_gift_nifty_gives_level_time_contracts_and_expiry():
    reading = read_gift_nifty(gift(), ist(8, 40))
    assert reading.complete and reading.source_time == ist(8, 39)
    assert reading.values == {"gift_level": "1234.5", "gift_contracts": "4321", "gift_expiry": "27-Oct-2026"}


@pytest.mark.parametrize(
    ("stamp", "complete"),
    [("22-Oct-2026 08:25", True), ("22-Oct-2026 08:24", False), ("21-Oct-2026 08:39", False),
     ("22-Oct-2026 08:41", True), ("22-Oct-2026 08:42", False)],
)  # fmt: skip
def test_gift_nifty_is_fresh_up_to_15_minutes_old_on_the_same_day(stamp, complete):
    """Seen at 08:40:00: 15 minutes old is fresh, 16 stale; yesterday stale; a minute ahead is NSE's rounding."""
    reading = read_gift_nifty(gift(stamp), ist(8, 40))
    assert reading.complete is complete and (complete or reading.detail.startswith("stale"))


@pytest.mark.parametrize("data", [b"<html>", b"[]", b'{"data": {}}', b'{"data": {"giftNifty": {"lastprice": 1}}}'])
def test_gift_nifty_outside_its_layout_is_refused(data):
    with pytest.raises(BadAnswer):
        read_gift_nifty(data, ist(8, 40))


def test_preopen_list_counts_stocks_with_an_iep():
    reading = read_preopen_list(fo_list(), DAY)
    assert reading.complete and reading.values == {"fo_stocks": "3", "fo_with_iep": "2"}
    assert reading.source_time == ist(9, 8, 43)


@pytest.mark.parametrize(
    ("data", "detail"),
    [(fo_list("21-Oct-2026 09:08:43"), "not final"), (fo_list("22-Oct-2026 09:07:59"), "not final"),
     (b'{"data": [], "msg": "No Data Found"}', "empty list")],
)  # fmt: skip
def test_preopen_list_of_another_day_before_0908_or_empty_is_incomplete(data, detail):
    reading = read_preopen_list(data, DAY)
    assert not reading.complete and reading.detail.startswith(detail)


def test_preopen_list_at_0908_exactly_is_final():
    assert read_preopen_list(fo_list("22-Oct-2026 09:08:00"), DAY).complete


@pytest.mark.parametrize("data", [b"not json", b'{"data": "x"}', b'{"data": [{"metadata": {}}], "timestamp": "x"}'])
def test_preopen_list_outside_its_layout_is_refused(data):
    with pytest.raises(BadAnswer):
        read_preopen_list(data, DAY)


def test_index_preopen_is_the_close_of_the_0909_candle_complete_at_0910():
    reading = read_index_preopen(candles(), DAY, "nifty")
    assert reading.complete and reading.values == {"nifty_preopen": "5555.5"}
    assert reading.source_time == ist(9, 10)


@pytest.mark.parametrize(
    ("data", "detail"),
    [(candles(count=9), "no 09:09 candle yet"), (candles(first=time(9, 15), count=5), "no pre-open value"),
     (candles(count=0), "no 09:09 candle yet"), (candles(day=DAY.replace(day=21)), "no 09:09 candle yet")],
)  # fmt: skip
def test_index_preopen_without_the_0909_candle_is_incomplete(data, detail):
    reading = read_index_preopen(data, DAY, "nifty")
    assert not reading.complete and reading.detail.startswith(detail) and reading.values == {}


@pytest.mark.parametrize(
    "data", [b'{"x": 1}', b'{"candles": [["2026-10-22T09:09:00+05:30", 1, 1, 1, 1]]}', b'{"candles": [["t"]]}']
)
def test_index_candles_outside_their_layout_are_refused(data):
    with pytest.raises(BadAnswer):
        read_index_preopen(data, DAY, "nifty")


def test_gift_nifty_from_before_midnight_is_stale_even_when_under_15_minutes_old():
    reading = read_gift_nifty(gift("21-Oct-2026 23:55"), ist(0, 5))
    assert not reading.complete and reading.detail.startswith("stale")
