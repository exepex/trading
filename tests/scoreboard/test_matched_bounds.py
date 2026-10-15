"""Story S3 criterion 8: bounds from S2's resampler, Holm on a plain list of p-values, the series days and the cut at an
open take."""

import random
from datetime import date, timedelta

from fno.scoreboard.matched import DayScore, pair_series, scored_days, series_of
from fno.scoreboard.matched_actions import SKIP, TAKE, Action
from fno.scoreboard.matched_days import NO_RUN, BookDay
from fno.scoreboard.series import DailySeries
from fno.scoreboard.standard_unit import CLOSED, OPEN, StandardResult
from fno.scoreboard.uncertainty import holm, lower_bound, p_value

DAY0 = date(2026, 1, 1)


def days(n):
    return tuple(DAY0 + timedelta(i) for i in range(n))


def series(nets, risks=None):
    return DailySeries(days(len(nets)), tuple(nets), tuple(risks or [1000.0] * len(nets)))


def test_holm_known_answer_passes_the_first_and_stops_at_the_second():
    assert holm([0.010, 0.030, 0.040]) == [True, False, False]  # 0.010 < 0.05/3; 0.030 >= 0.05/2: stop
    assert holm([0.040, 0.010, 0.030]) == [False, True, False]  # same claims, any order
    assert holm([0.049]) == [True] and holm([0.05]) == [False] and holm([]) == []


def test_the_p_value_is_below_5_percent_exactly_when_the_lower_bound_is_above_zero():
    rng = random.Random(7)
    for shift in (-40.0, -5.0, 0.0, 5.0, 12.0, 40.0):
        s = series([rng.gauss(shift, 100.0) for _ in range(60)])
        assert (p_value(s, resamples=2000) < 0.05) == (lower_bound(s, resamples=2000) > 0)


def test_a_series_needs_one_whole_block_of_20_days():
    assert lower_bound(series([10.0] * 19)) is None and p_value(series([10.0] * 19)) is None
    assert lower_bound(series([10.0] * 20)) == 0.01 and p_value(series([10.0] * 20)) == 0.0


def test_the_pair_bound_is_the_mean_difference_on_risk_1():
    first = [DayScore(d, n, 1.0, False) for d, n in zip(days(20), range(20), strict=True)]
    second = [DayScore(d, 1.0, 1.0, False) for d in days(20)]
    pair = pair_series(first, second)
    assert pair.risk == (1.0,) * 20 and pair.net_per_risk == sum(range(20)) / 20 - 1
    assert lower_bound(pair) == lower_bound(DailySeries(pair.days, pair.net, (1.0,) * 20))


def book_day(day, kind=SKIP, reason=""):
    actions = {"O": Action(kind, "x", {})} if kind else {}
    return BookDay("book1_rules", day, reason, actions)


def test_25_sessions_with_3_not_observed_and_10_skip_only_give_a_22_day_series():
    all_days = days(25)
    book_days = [book_day(d, None, NO_RUN) if i < 3 else book_day(d, SKIP if i < 13 else None)
                 for i, d in enumerate(all_days)]  # fmt: skip
    scores = scored_days(book_days, {})
    assert len(scores) == 22 and all((s.net, s.risk) == (0.0, 0.0) for s in scores[:10])


def test_a_day_with_an_open_take_ends_the_series():
    d0, d1, d2 = days(3)
    results = {("book1_rules", d0, "O"): StandardResult(CLOSED, 1000.0, 5000.0),
               ("book1_rules", d1, "O"): StandardResult(OPEN, max_loss=4000.0),
               ("book1_rules", d2, "O"): StandardResult(CLOSED, 300.0, 2000.0)}  # fmt: skip
    scores = scored_days([book_day(d, TAKE) for d in (d0, d1, d2)], results)
    assert series_of(scores) == DailySeries((d0,), (1000.0,), (5000.0,))  # open cut, never 0; later days wait
