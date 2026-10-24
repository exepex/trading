"""Criteria 3-4: hand bin frequencies and Brier; unsettled expiries left out and counted; a close equal to K is not
above; the bootstrap resamples expiries, never rows."""

from datetime import date

import pytest

from fno.itm_chance.calibration import table
from fno.itm_chance.chances import expiry_chances
from fno.itm_chance.publish import encode
from fno.itm_chance.report import calibration_report, regime_start
from fno.itm_chance.rows import Row, bin_of, bucket_of, of_source, rows_for
from fno.itm_chance.settlement import Settled

from .builders import expiry, record

E1, E2 = date(2026, 1, 27), date(2026, 2, 24)


def settled(expiry_day, price) -> Settled:
    return Settled("NIFTY", expiry_day, price, "e7", price, None)


def row(expiry_day, p, y, days=10, source="backfill_eod", day=date(2026, 1, 15), strike=1.0) -> Row:
    return Row(day, expiry_day, days, source, strike, p, y)


def test_rows_use_body_strikes_once_with_the_call_chance_and_equal_is_not_above():
    chances = expiry_chances(record(date(2026, 1, 15), [expiry(E1, 12, strikes=(22500.0, 23000.0, 21000.0))]))
    rows = rows_for(chances, {E1: settled(E1, 23000.0)})
    assert [(r.strike, round(r.p, 6), r.y) for r in rows] == [(22500.0, 0.7, 1), (23000.0, 0.45, 0)]


def test_an_unsettled_expiry_gives_no_rows_and_is_counted_with_its_issue_days():
    records = [record(date(2026, 1, 15), [expiry(E1, 12), expiry(E2, 40)])]
    found = {E1: settled(E1, 23100.0), E2: Settled("NIFTY", E2, None, None, None, "no settlement file yet")}
    report = calibration_report("NIFTY", records, lambda u, e: found[e], date(2026, 3, 1), {"g13": "x"})
    assert report["settled_expiries"] == [E1.isoformat()] and report["slices"]["all"]["expiries"] == 1
    assert report["left_out"] == [{"expiry": E2.isoformat(), "price": None, "source": None, "official_close": None,
                                   "problem": "no settlement file yet", "issue_days": 1}]  # fmt: skip


def test_only_expiries_up_to_as_of_are_asked():
    asked = []
    records = [record(date(2026, 1, 15), [expiry(E1, 12), expiry(E2, 40)])]
    calibration_report("NIFTY", records, lambda u, e: asked.append(e) or settled(e, 1.0), E1, {})
    assert asked == [E1]


def test_hand_frequencies_brier_and_reliability():
    rows = [row(E1, 0.10, 0), row(E1, 0.12, 1), row(E2, 0.60, 1), row(E2, 0.58, 0)]
    bucket = table(rows)["buckets"][bucket_of(10)]
    bins = {b["bin"]: b for b in bucket["bins"]}
    assert bins["[0.05, 0.15)"]["frequency"] == 0.5 and bins["[0.05, 0.15)"]["mean_chance"] == pytest.approx(0.11)
    assert bins["[0.55, 0.65)"]["frequency"] == 0.5 and bins["[0.55, 0.65)"]["expiries"] == 1
    brier = (0.10**2 + 0.88**2 + 0.40**2 + 0.58**2) / 4
    reliability = (2 * (0.11 - 0.5) ** 2 + 2 * (0.59 - 0.5) ** 2) / 4
    assert bucket["brier"] == pytest.approx(brier, abs=1e-6) and bucket["reliability"] == pytest.approx(reliability)
    assert bucket["expiries"] == 2 and bucket["rows"] == 4


def test_bins_and_buckets_edges():
    assert [bin_of(p) for p in (0.0, 0.0499, 0.05, 0.95, 1.0)] == [0, 0, 1, 10, 10]
    assert [bucket_of(d) for d in (1, 7, 8, 21, 22, 45, 46, 300)] == [0, 0, 1, 1, 2, 2, 3, 3]


def intervals(rows):
    bucket = table(rows)["buckets"][bucket_of(10)]
    return bucket["brier_interval_95"], [b["frequency_interval_95"] for b in bucket["bins"]]


def test_one_expiry_has_no_spread_however_many_rows_it_has():
    one = [row(E1, 0.10, 0), row(E1, 0.12, 1)] * 50
    brier, frequencies = intervals(one)
    assert brier[0] == brier[1] and all(f[0] == f[1] for f in frequencies)


def test_repeating_every_row_of_every_expiry_leaves_the_intervals_unchanged():
    base = [row(e, p, y) for e in (E1, E2, date(2026, 3, 31)) for p, y in ((0.1, 0), (0.12, 1), (0.6, 1))]
    assert intervals(base) == intervals(base * 7)


def test_all_takes_one_source_per_day_and_expiry_3pm_first():
    rows = [row(E1, 0.1, 0, source="backfill_eod"), row(E1, 0.2, 0, source="3pm"),
            row(E1, 0.3, 0, source="backfill_eod", day=date(2026, 1, 16))]  # fmt: skip
    assert [r.p for r in of_source(rows, "all")] == [0.2, 0.3]
    assert [r.p for r in of_source(rows, "backfill_eod")] == [0.1, 0.3]


def test_the_expiry_day_change_is_read_from_the_expiries():
    thursdays = [date(2025, 7, 31), date(2025, 8, 28)]
    assert regime_start([*thursdays, date(2025, 9, 30), date(2025, 10, 28)]) == date(2025, 9, 30)
    assert regime_start(thursdays) is None
    stray = [date(2024, 1, 25), date(2024, 2, 27), date(2024, 3, 28)]  # a holiday-moved Tuesday, then Thursdays
    assert regime_start([*stray, date(2025, 9, 30)]) == date(2025, 9, 30)


def test_the_report_is_byte_identical_on_a_rerun():
    records = [record(date(2026, 1, 15), [expiry(E1, 12)])]
    make = lambda: calibration_report("NIFTY", records, lambda u, e: settled(e, 23100.0), E2, {"g13": "x"})  # noqa: E731
    assert encode(make()) == encode(make())


def test_expiries_with_different_outcomes_give_a_spread():
    rows = [row(e, 0.5, y) for e, y in ((E1, 0), (E2, 1), (date(2026, 3, 31), 1), (date(2026, 4, 28), 0))]
    brier, (frequency,) = intervals(rows)
    assert frequency[0] < 0.5 < frequency[1] and brier[0] == brier[1] == 0.25
