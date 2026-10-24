"""Story A4c-2, round 2 (judge 571 minor 2): A4's early limit is one rule, `earliest_waiting_moment`, which both the
recorder's and the index runner's "too early" decisions call; today's edges are kept to the second."""

from datetime import date, datetime, time

import pytest

from fno.models import IST
from fno.quotes.recorder import earliest_waiting_moment, earliest_waiting_start
from tests.quotes.test_quote_recorder import FakeProvider, recorder
from tests.quotes.test_recorder_calendar import NoCalls
from tests.quotes.window_fakes import at, named_recorder

DAY = date(2026, 10, 13)


@pytest.mark.parametrize(("start", "status"), [((14, 34, 59), "recorded"), ((14, 34, 58), "too early")])
def test_a4_s_window_waits_from_1435_and_one_second_before_is_too_early(tmp_path, start, status):
    """The fake clock moves 1 s at each read: a clock set at 14:34:59 reads 14:35:00 first."""
    rec, _ = recorder(tmp_path, FakeProvider(), datetime(2026, 10, 13, *start, tzinfo=IST))
    assert rec.record().status == status


@pytest.mark.parametrize(("start", "too_early"), [((13, 59, 59), False), ((13, 59, 58), True)])
def test_a_named_window_keeps_its_own_longer_wait(tmp_path, start, too_early):
    """A4e's v4 window (14:30, 30 minutes early): 14:00:00 waits, 13:59:59 is too early and asks nothing (the fake
    clock moves 1 s at each read, so a clock set at 13:59:59 reads 14:00:00 first)."""
    rec, _, _ = named_recorder(tmp_path, at(*start), provider=NoCalls() if too_early else None)
    assert (rec.record().status == "too early") is too_early


def test_the_rule_is_the_window_start_less_the_wait_on_the_real_day():
    assert earliest_waiting_moment(DAY, time(15, 1)) == datetime(2026, 10, 13, 14, 41, tzinfo=IST)
    assert earliest_waiting_moment(DAY, time(14, 30), 30 * 60) == datetime(2026, 10, 13, 14, 0, tzinfo=IST)
    assert earliest_waiting_moment(DAY, time(14, 30), 0) == datetime(2026, 10, 13, 14, 30, tzinfo=IST)


def test_a_wait_longer_than_the_time_of_day_lands_on_the_day_before_and_never_fails():
    """The config allows any whole number of minutes (fno/quotes/window.py): 900 minutes before 14:30 is 23:30 the day
    before, so every run that day waits, as the old `start - now > wait` test said. Computed from `date.min`, as the
    time-of-day function does, it would raise OverflowError instead."""
    assert earliest_waiting_moment(DAY, time(14, 30), 900 * 60) == datetime(2026, 10, 12, 23, 30, tzinfo=IST)


def test_the_time_of_day_is_the_same_rule_down_to_its_midnight_limit():
    """Criterion 8 (14:41 and 14:35) is `test_index_recording.py`'s; here the earliest window it can serve."""
    assert earliest_waiting_start(time(0, 20)) == time(0, 0)
