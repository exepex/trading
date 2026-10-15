"""FT1 criteria 4 and 5 (days): E8's fill times, nights across a weekend and a holiday, the decision days left out and
the expiry more than 7 sessions away (PROTOCOL.md sections 4-6)."""

from datetime import date, time

import pytest
from ft1study.days import NEXT_NOT_REGULAR, NOT_REGULAR, Schedule
from ft1study.times import DECISION_14, DECISION_15, Moment, fill_moment, is_e4_snapshot, nights

from tests.research_ft1.ft1_fakes import FakeCalendar, contracts

WED, THU, FRI, MON = date(2025, 1, 8), date(2025, 1, 9), date(2025, 1, 10), date(2025, 1, 13)
CAL = FakeCalendar()


@pytest.mark.parametrize(("reaction", "day", "at"), [(5, WED, time(15, 15)), (30, THU, time(9, 45)),
                                                     (60, THU, time(10, 15))])  # fmt: skip
def test_a_15_00_decision_fills_at_15_15_then_next_09_45_and_10_15(reaction, day, at):
    assert fill_moment(Moment(WED, DECISION_15), reaction, CAL.next_session) == Moment(day, at)


@pytest.mark.parametrize(("reaction", "at"), [(5, time(14, 15)), (30, time(14, 45)), (60, time(15, 15))])
def test_a_14_00_decision_fills_the_same_day_at_14_15_14_45_and_15_15(reaction, at):
    assert fill_moment(Moment(WED, DECISION_14), reaction, CAL.next_session) == Moment(WED, at)


def test_a_friday_decision_fills_on_monday_after_3_nights_and_a_holiday_moves_it_on():
    fill = fill_moment(Moment(FRI, DECISION_15), 60, CAL.next_session)
    assert fill == Moment(MON, time(10, 15)) and nights(Moment(FRI, DECISION_15), fill) == 3
    holiday = FakeCalendar(holidays={MON})
    later = fill_moment(Moment(FRI, DECISION_15), 30, holiday.next_session)
    assert later == Moment(date(2025, 1, 14), time(9, 45)) and nights(Moment(FRI, DECISION_15), later) == 4


def test_e4s_15_15_snapshot_is_the_15_00_r5_and_the_14_00_r60_fill_only():
    flags = {(at, r): is_e4_snapshot(fill_moment(Moment(WED, at), r, CAL.next_session), Moment(WED, at))
             for at in (DECISION_15, DECISION_14) for r in (5, 30, 60)}  # fmt: skip
    assert {k for k, v in flags.items() if v} == {(DECISION_15, 5), (DECISION_14, 60)}


def test_the_price_at_a_mark_is_the_close_of_the_candle_starting_15_minutes_earlier():
    assert Moment(WED, time(15, 0)).candle_start.time() == time(14, 45)
    assert Moment(WED, time(10, 15)).candle_start.time() == time(10, 0)


EXPIRY_1, EXPIRY_2 = date(2025, 1, 30), date(2025, 2, 27)


def schedule(calendar):
    return Schedule(calendar, contracts([EXPIRY_1, EXPIRY_2], date(2025, 1, 1), date(2025, 2, 27), calendar))


def test_an_entry_7_or_fewer_sessions_before_expiry_takes_the_next_expiry():
    days, _ = schedule(CAL).decision_days(date(2025, 1, 20), date(2025, 1, 21))
    by_day = {d.day: d for d in days}
    assert by_day[date(2025, 1, 20)].expiry == EXPIRY_1  # 21-24, 27-30: 8 sessions after it
    assert by_day[date(2025, 1, 20)].sessions_to_expiry == 8
    assert by_day[date(2025, 1, 21)].expiry == EXPIRY_2  # only 7 sessions to 30 Jan


def test_special_and_muhurat_days_and_days_before_them_are_left_out_and_counted():
    special_saturday, muhurat_friday = date(2025, 1, 18), date(2025, 1, 24)
    calendar = FakeCalendar(kinds={special_saturday: "special", muhurat_friday: "muhurat"})
    days, left_out = schedule(calendar).decision_days(date(2025, 1, 16), date(2025, 1, 24))
    kept = {d.day for d in days}
    assert special_saturday not in kept and muhurat_friday not in kept
    assert date(2025, 1, 17) not in kept and date(2025, 1, 23) not in kept  # their next session is not regular
    assert left_out == {NOT_REGULAR: 2, NEXT_NOT_REGULAR: 2}
    assert kept == {date(2025, 1, 16), date(2025, 1, 20), date(2025, 1, 21), date(2025, 1, 22)}
