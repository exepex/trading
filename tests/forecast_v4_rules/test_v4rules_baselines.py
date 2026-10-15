"""Story G7: base rate, EWMA, HAR and trailing (PROTOCOL_v4.md section 3.1), point in time."""

from datetime import date, datetime, timedelta

import numpy as np
import pytest

from fno.forecast_v4_rules.baselines import (
    MISSING,
    NOT_ELIGIBLE,
    OK,
    BaseRate,
    Ewma,
    Har,
    Value,
    trailing_previous_session,
)
from fno.forecast_v4_rules.series import DayValue, Outcome, SessionRv

START = date(2020, 1, 1)


def days(n):
    return [START + timedelta(days=i) for i in range(n)]


def outcomes(n, ones=0):
    """n outcomes, each resolved the day after its own, the first `ones` of them 1."""
    return [Outcome(d, i < ones, d + timedelta(days=1)) for i, d in enumerate(days(n))]


def test_base_rate_needs_500_resolved_outcomes_and_uses_the_latest_750():
    found = outcomes(1000, ones=250)
    rate = BaseRate(found)
    cutoff_500 = found[499].resolved_on + timedelta(days=1)  # 500 resolved before this day
    assert rate.forecast(cutoff_500 - timedelta(days=1)).status == NOT_ELIGIBLE  # 499
    assert rate.forecast(cutoff_500) == Value(OK, 250 / 500)
    last = found[-1].resolved_on + timedelta(days=1)
    assert rate.forecast(last) == Value(OK, 0 / 750)  # the 750 most recent hold no 1s
    assert BaseRate([]).forecast(START).status == NOT_ELIGIBLE


def test_an_outcome_resolved_on_the_forecast_day_is_not_yet_known():
    found = outcomes(500)
    day = found[-1].resolved_on
    assert BaseRate(found).forecast(day).status == NOT_ELIGIBLE
    assert BaseRate(found).forecast(day + timedelta(days=1)).status == OK


def rv_series(values):
    return [DayValue(d, v) for d, v in zip(days(len(values)), values, strict=True)]


def test_ewma_seeds_with_the_mean_of_250_and_updates_by_lambda():
    values = [1e-4] * 250 + [5e-4, 2e-4]
    ewma = Ewma(rv_series(values))
    d250, d251, d252 = days(252)[249], days(252)[250], days(252)[251]
    assert ewma.variance(d250) is None  # only 249 sessions before it
    assert ewma.forecast(d251, 1).value == pytest.approx(1e-4)  # the seed, at the 250th session
    expected = 0.94 * (0.94 * 1e-4 + 0.06 * 5e-4) + 0.06 * 2e-4
    assert ewma.forecast(d252 + timedelta(days=1), 5).value == pytest.approx(5 * expected)
    assert Ewma(rv_series([1e-4] * 249)).forecast(d252, 1).status == NOT_ELIGIBLE


def har_by_hand(values, refit_index, d_index, minimum):
    rows, targets = [], []
    for t in range(22, len(values) - 1):
        if t + 1 >= refit_index:
            break
        rows.append([1, values[t - 1], np.mean(values[t - 5 : t]), np.mean(values[t - 22 : t])])
        targets.append(values[t + 1])
    beta = np.linalg.lstsq(np.array(rows[-750:]), np.array(targets[-750:]), rcond=None)[0]
    x = [1, values[d_index - 1], np.mean(values[d_index - 5 : d_index]), np.mean(values[d_index - 22 : d_index])]
    return float(np.dot(beta, x)), len(rows)


def test_har_rebuilds_by_hand_and_refits_on_the_first_session_of_the_month():
    rng = np.random.default_rng(7)
    values = list(1e-4 * (1 + rng.random(120)))
    rv = rv_series(values)
    sessions = [r.day for r in rv]
    d = date(2020, 4, 20)  # refit day: 1 Apr 2020 (index 91)
    expected, n = har_by_hand(values, 91, sessions.index(d), 10)
    assert Har(rv, 1, sessions, minimum=10).forecast(d) == Value(OK, pytest.approx(expected))
    assert Har(rv, 1, sessions, minimum=n + 1).forecast(d).status == NOT_ELIGIBLE  # one row short
    assert Har(rv, 1, sessions, minimum=n).forecast(d).status == OK


def test_har_ignores_everything_from_the_forecast_day_on():
    rng = np.random.default_rng(3)
    values = list(1e-4 * (1 + rng.random(120)))
    sessions = days(120)
    d = date(2020, 4, 20)
    before = Har(rv_series(values), 1, sessions, minimum=10).forecast(d)
    changed = values[: sessions.index(d)] + [9e-3] * (120 - sessions.index(d))
    assert Har(rv_series(changed), 1, sessions, minimum=10).forecast(d) == before


def test_a_forecast_that_is_not_strictly_positive_is_missing():
    assert Value.of(0.0) == Value(MISSING) and Value.of(-1e-6) == Value(MISSING) and Value.of(None) == Value(MISSING)
    assert Value.of(0.0, positive=False) == Value(OK, 0.0)


def session(day, value):
    return SessionRv(day, value, datetime(day.year, day.month, day.day, 16, 0))


def test_trailing_is_the_previous_session_and_missing_when_it_is_void():
    rows = [session(date(2026, 10, 15), 1e-4), session(date(2026, 10, 16), None)]
    assert trailing_previous_session(rows, date(2026, 10, 15)) == Value(OK, 1e-4)
    assert trailing_previous_session(rows, date(2026, 10, 16)) == Value(MISSING)  # void: never an older session
    assert trailing_previous_session(rows, date(2026, 10, 19)) == Value(MISSING)  # no row at all
    assert trailing_previous_session([], None) == Value(MISSING)
