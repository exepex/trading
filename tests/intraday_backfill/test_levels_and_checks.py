"""Story A16b, criteria 2 and 5 (pure parts): the 26 levels from 15-minute candles, the per-session 1-minute check and
the check against NSE's official range. Every level is fake."""

from datetime import date

import pytest

from fno.intraday.candle_levels import CandleParse, parse_candles, session_candles
from fno.intraday.minute_check import check_minutes
from fno.intraday.nse_range import NseDay, check_range, read_nse_day
from tests.intraday_backfill.fakes import fifteen_minute_rows, levels, minute_rows, nse_day

DAY = date(2026, 10, 14)
VALUES = levels(DAY)


def candles(rows):
    return session_candles(DAY, parse_candles(rows))


def test_a_full_session_gives_the_0915_open_and_the_25_closes_and_counts_the_others():
    found = candles(fifteen_minute_rows(DAY, VALUES))
    assert list(found.levels) == VALUES and found.missing == 0 and len(found.used) == 25
    assert found.outside == 2  # the 09:00 pre-open and 15:30 candles are never levels
    assert found.basis_counts == "candle_15m_open:1;candle_15m_close:25"


@pytest.mark.parametrize(("dropped", "none_at"), [((0,), (0, 1)), ((24,), (25,)), ((12,), (13,))])
def test_a_missing_candle_leaves_its_levels_none_never_filled(dropped, none_at):
    found = candles(fifteen_minute_rows(DAY, VALUES, drop=dropped))
    assert found.missing == 1 and [i for i, v in enumerate(found.levels) if v is None] == list(none_at)


def test_candles_at_times_that_are_not_marks_or_of_another_day_are_not_levels():
    rows = fifteen_minute_rows(DAY, VALUES) + [[f"{DAY}T15:45:00", 1, 1, 1, 1, None, None]]
    rows += [["2026-10-13T09:15:00", 1, 1, 1, 1, None, None], [f"{DAY}T10:07:00", 1, 1, 1, 1, None, None]]
    found = candles(rows)
    assert list(found.levels) == VALUES and found.outside == 4


def test_an_empty_answer_is_25_missing_and_a_bad_time_is_a_parse_failure():
    assert candles([]).missing == 25 and set(candles([]).levels) == {None}
    with pytest.raises(CandleParse):
        parse_candles([["2026-10-14T09:15:00+05:30", 1, 1, 1, 1]])
    with pytest.raises(CandleParse):
        parse_candles([["not a time", 1, 1, 1, 1]])


def test_the_minute_check_passes_at_005_and_voids_at_006():
    minutes = parse_candles(minute_rows(DAY, VALUES, 19990.0))
    assert check_minutes(DAY, tuple(VALUES), minutes).mismatched == ()
    shifted = list(VALUES)
    shifted[5] += 0.05
    assert check_minutes(DAY, tuple(shifted), minutes).mismatched == ()
    shifted[5] += 0.01
    assert check_minutes(DAY, tuple(shifted), minutes).mismatched == ("10:30",)
    opened = [VALUES[0] + 0.06, *VALUES[1:]]
    assert check_minutes(DAY, tuple(opened), minutes).mismatched == ("09:15",)  # the open against the 09:15 open


def test_the_minute_check_names_missing_minutes_and_reads_the_last_pre_open_close():
    minutes = parse_candles(minute_rows(DAY, VALUES, 19990.0, skip=("10:29", "09:15")))
    found = check_minutes(DAY, tuple(VALUES), minutes)
    assert found.missing == ("09:15", "10:29") and found.pre_open_close == 19990.0
    assert check_minutes(DAY, tuple(VALUES), []).pre_open_close is None


def test_a_level_or_a_candle_high_or_low_outside_nse_by_more_than_005_voids():
    found = candles(fifteen_minute_rows(DAY, VALUES))
    nse = nse_day(DAY, VALUES)
    assert not check_range(found.levels, found.used, nse, None).outside
    assert not check_range(found.levels, found.used, NseDay(nse.open, nse.high - 0.05, nse.low), None).outside
    assert check_range(found.levels, found.used, NseDay(nse.open, nse.high - 0.06, nse.low), None).outside
    assert check_range(found.levels, found.used, NseDay(nse.open, nse.high, nse.low + 0.06), None).outside


def test_one_high_19630_above_nse_voids_although_every_close_is_inside():
    rows = fifteen_minute_rows(DAY, VALUES)
    nse = nse_day(DAY, VALUES)
    rows[5][2] = nse.high + 196.30  # the 23 Mar 2020 shape
    found = candles(rows)
    assert all(nse.low <= v <= nse.high for v in found.levels)
    checked = check_range(found.levels, found.used, nse, None)
    assert checked.outside and checked.high_gap == -196.30


def test_the_gaps_are_differences_and_the_open_gap_needs_a_1_minute_answer():
    found = candles(fifteen_minute_rows(DAY, VALUES))
    nse = nse_day(DAY, VALUES)
    checked = check_range(found.levels, found.used, nse, nse.open + 0.25)
    assert (checked.high_gap, checked.low_gap, checked.open_gap) == (0.0, 0.0, 0.25)
    assert check_range(found.levels, found.used, nse, None).open_gap is None
    assert check_range((None,) * 26, (), nse, None).high_gap is None


def test_nse_s_file_gives_nifty_50_and_a_file_without_it_is_refused():
    text = "Index Name,Index Date,Open Index Value,High Index Value,Low Index Value\nNifty 50,14-10-2026,1,3,0.5\n"
    assert read_nse_day(text.encode()) == NseDay(1.0, 3.0, 0.5)
    with pytest.raises(ValueError):
        read_nse_day(b"Index Name,Open Index Value\nNifty Bank,1\n")
