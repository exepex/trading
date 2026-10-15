"""Story A16b, criteria 3, 4 and 6 (rows): the rule-5 sessions from step 0's real counts, A16's arithmetic shared with
a hand computation, written once, and provenance at the next session's 09:15 boundary. Every level is fake."""

from datetime import date, datetime

import pytest

from fno.intraday.candle_archive import ArchivedCopy
from fno.intraday.candle_levels import parse_candles, session_candles
from fno.intraday.candle_rv_table import CandleRvTable
from fno.intraday.nse_days import NseReading
from fno.intraday.realised_vol import CandleCloseRv15m, QuoteSnapshotRv15m
from fno.intraday.rv_table import ALREADY, WRITTEN, RvConflict
from fno.intraday.session_deriver import SessionInputs
from fno.models import IST
from tests.intraday_backfill.fakes import (
    _next_session,
    build,
    fifteen_minute_rows,
    levels,
    minute_rows,
    nse_day,
    t,
)


def _rows_with(day: date, present: int, after_close: int = 0) -> list:
    """`present` of the 25 session candles (the first ones), then `after_close` candles from 15:45 on."""
    rows = fifteen_minute_rows(day, levels(day), drop=tuple(range(present, 25)), extra=False)
    value, starts = levels(day)[0], [15 * 60 + 45 + 15 * k for k in range(after_close)]  # minutes after midnight
    return rows + [[t(day, m // 60, m % 60), value, value, value, value, None, None] for m in starts]


@pytest.mark.parametrize(
    ("day", "present", "after_close", "reason"),
    [
        (date(2020, 3, 13), 23, 0, "missing_candles:2"),  # step 0: 23 of 25
        (date(2020, 3, 23), 23, 0, "missing_candles:2"),
        (date(2021, 2, 24), 5, 4, "missing_candles:20"),  # the halt day: its candles after 15:30 are not levels
        (date(2024, 3, 2), 10, 0, "missing_candles:15"),  # short special sessions
        (date(2024, 5, 18), 10, 0, "missing_candles:15"),
        (date(2025, 9, 26), 22, 0, "missing_candles:3"),  # Groww's holes
        (date(2026, 9, 29), 20, 0, "missing_candles:5"),
        (date(2025, 10, 10), 0, 0, "missing_candles:25"),
    ],
)
def test_the_rule_5_sessions_give_their_named_void_reasons(day, present, after_close, reason):
    found = session_candles(day, parse_candles(_rows_with(day, present, after_close)))
    assert f"missing_candles:{found.missing}" == reason and found.outside == after_close
    assert sum(level is not None for level in found.levels) == (present + 1 if present else 0)


def test_the_candle_rule_gives_a16_s_numbers_and_a_hand_computation():
    marks_levels = [100.0] * 26
    marks_levels[1] = 101.0  # up 1% and back: two squared log returns of ln(1.01)
    candle, quote = CandleCloseRv15m().compute(marks_levels, 99.0), QuoteSnapshotRv15m().compute(marks_levels, 99.0)
    assert candle == quote
    assert candle.intraday == pytest.approx(1.980181681750e-4, rel=1e-12)  # 2 * ln(1.01)^2
    assert candle.overnight == pytest.approx(1.010092507682e-4, rel=1e-12)  # ln(100/99)^2
    assert candle.vol_pct == pytest.approx(1.7292409286829, rel=1e-12)
    assert CandleCloseRv15m().method != QuoteSnapshotRv15m().method  # one arithmetic, two named rules


def test_a_missing_level_voids_only_the_part_that_needs_it():
    some = levels(date(2026, 10, 14))
    assert CandleCloseRv15m().compute([None, *some[1:]], 20000.0).overnight is None
    middle = CandleCloseRv15m().compute([*some[:5], None, *some[6:]], 20000.0)
    assert middle.intraday is None and middle.overnight is not None and middle.session is None


def test_a_row_is_written_once_the_same_inputs_change_nothing_and_others_are_refused(tmp_path):
    table = CandleRvTable(tmp_path)
    row = {field: "" for field in table.fields} | {"session": "2026-10-14", "method": "m", "inputs_sha256": "a" * 64}
    assert table.write_once(row) == WRITTEN and table.write_once(dict(row)) == ALREADY
    with pytest.raises(RvConflict, match="2026-10-14"):
        table.write_once(row | {"inputs_sha256": "b" * 64})
    assert table.row(date(2026, 10, 14))["inputs_sha256"] == "a" * 64
    assert (
        table.path(date(2026, 10, 14)).relative_to(tmp_path).as_posix() == "rv-candle/2026/nifty_rv_candle_20261014.csv"
    )


def _derived(tmp_path, day: date, fetched: datetime, window_fetched: datetime | None = None) -> dict:
    values = levels(day)
    window = ArchivedCopy("15m", day, day, "w", "a" * 64, window_fetched or fetched, fifteen_minute_rows(day, values))
    minutes = ArchivedCopy("1m", day, day, "m", "b" * 64, fetched, minute_rows(day, values, values[0] - 3.0))
    deriver = build(tmp_path, None, None).deriver
    return deriver.derive(SessionInputs(day, window, minutes, NseReading(nse_day(day, values), "c" * 64), 20000.0))


@pytest.mark.parametrize(
    ("day", "seen", "expected"),
    [
        (date(2026, 10, 14), datetime(2026, 10, 14, 18, 0), "live"),  # the same evening
        (date(2026, 10, 14), datetime(2026, 10, 15, 9, 14, 59), "live"),  # boundary: before the next 09:15
        (date(2026, 10, 14), datetime(2026, 10, 15, 9, 15, 0), "backfilled"),
        (date(2026, 9, 25), datetime(2026, 9, 28, 9, 14, 59), "live"),  # across a weekend
        (date(2026, 10, 1), datetime(2026, 10, 3, 12, 0), "live"),  # 2 Oct holiday, then the weekend
        (date(2026, 10, 1), datetime(2026, 10, 5, 9, 15, 0), "backfilled"),
        (date(2026, 10, 9), datetime(2026, 10, 10, 9, 15, 0), "backfilled"),  # the special Saturday session counts
        (date(2026, 10, 14), datetime(2026, 10, 30, 18, 0), "backfilled"),
    ],
)
def test_provenance_comes_from_a17_with_the_next_session_s_0915_as_the_boundary(tmp_path, day, seen, expected):
    seen = seen.replace(tzinfo=IST)
    row = _derived(tmp_path, day, seen)
    assert row["provenance"] == expected and row["status"] == "ok"
    assert _next_session(date(2026, 10, 1)) == date(2026, 10, 5)


def test_first_seen_is_the_latest_copy_s_fetch_time(tmp_path):
    earlier = datetime(2026, 10, 14, 18, 0, tzinfo=IST)
    row = _derived(tmp_path, date(2026, 10, 14), datetime(2026, 10, 15, 9, 15, tzinfo=IST), window_fetched=earlier)
    assert row["first_seen_at"] == "2026-10-15T03:45:00+00:00" and row["provenance"] == "backfilled"
