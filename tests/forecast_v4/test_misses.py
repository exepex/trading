"""Story G9 (protocol v4 revision 9): missed days are counted, never imputed; too many misses, or any miss of a scarce
2% day, make a member "undecided, operations", which is never a claim and never futile."""

from datetime import date, timedelta

import pytest

from fno.forecast_v4.misses import MissReport, miss_report
from fno.forecast_v4.pairs import DatedForecasts

START = date(2025, 1, 1)


def rows(n, missed=(), both_missing=(), before=0, big=()):
    """n resolved days; the forecaster starts on day `before`; `missed`: forecaster absent, baseline present."""
    out = []
    for i in range(n):
        forecast = None if i < before or i in missed or i in both_missing else 0.3
        baseline = None if i in both_missing else 0.2
        out.append(DatedForecasts(START + timedelta(days=i), forecast, baseline, i % 2 == 0))
    return out, (lambda d: (d - START).days in big)


def test_misses_input_failures_and_days_before_the_first_forecast_are_counted_apart():
    found, big = rows(30, missed={12, 20}, both_missing={15}, before=5, big={12, 25})
    assert miss_report(found, big) == MissReport(observable=24, missed=2, big_observable=2, big_missed=1,
                                                 input_failures=1)  # fmt: skip


def test_unresolved_and_void_days_are_neither_observable_nor_missed():
    found, big = rows(10, missed={3})
    found[3] = DatedForecasts(found[3].day, None, 0.2, None)  # unresolved
    found[4] = DatedForecasts(found[4].day, None, 0.2, True, void=True)
    assert miss_report(found, big) == MissReport(8, 0, 0, 0, 0)


def test_a_forecaster_that_never_forecast_has_not_started():
    found, big = rows(20, before=20)
    assert miss_report(found, big) == MissReport(0, 0, 0, 0, 0) and not miss_report(found, big).operations_undecided


@pytest.mark.parametrize(("observable", "missed", "undecided"), [(100, 10, False), (100, 11, True), (125, 12, False),
                                                                 (125, 13, True)])  # fmt: skip
def test_the_overall_cap_is_10_percent(observable, missed, undecided):
    assert MissReport(observable, missed, 20, 0, 0).operations_undecided == undecided


BIG_DAY_CASES = [(9, 0, False), (9, 1, True), (10, 1, False), (10, 2, True), (25, 2, False), (25, 3, True)]


@pytest.mark.parametrize(("big_observable", "big_missed", "undecided"), BIG_DAY_CASES)
def test_the_2_percent_day_cap_allows_no_miss_below_ten_such_days(big_observable, big_missed, undecided):
    assert MissReport(200, big_missed, big_observable, big_missed, 0).operations_undecided == undecided


def test_the_line_names_every_count_and_the_verdict():
    assert MissReport(125, 13, 9, 1, 2).line() == (
        "misses: 13 of 125 baseline days (10.4%), 1 of 9 2% days; input failures: 2; undecided, operations"
    )
