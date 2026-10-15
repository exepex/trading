"""E8 rules 2 and 8, acceptance 1 and 7: the due mark of an order from its card time, R and the calendar."""

from __future__ import annotations

from datetime import date, time

import pytest

from fno.desk.owner_timing.availability import AlwaysAvailable
from fno.desk.owner_timing.clock import ExecutionSnapshotClock, OwnerTimingClock
from fno.desk.owner_timing.outcomes import ENTRY, EXIT, MISSED_OWNER_AWAY, DueMark, Missed
from tests.desk_owner_timing.fakes import CALENDAR, AwayDays, ist

THU, FRI, MON, WED = date(2026, 10, 15), date(2026, 10, 16), date(2026, 10, 19), date(2026, 10, 21)  # 20th: holiday


def clock(minutes: int, availability=None) -> OwnerTimingClock:
    return OwnerTimingClock(minutes, CALENDAR, availability or AlwaysAvailable())


@pytest.mark.parametrize(("minutes", "mark"), [(5, (9, 30)), (30, (9, 45)), (60, (10, 15))])
def test_a_card_after_the_snapshot_fills_the_next_morning(minutes, mark):
    # O1 posts the card after 15:15: R = 5 needs 15:30, after 15:25, so even it moves to the next session
    assert clock(minutes).due(ist(THU, 15, 16), ENTRY) == DueMark(FRI, ist(FRI, *mark))


@pytest.mark.parametrize(("minutes", "mark"), [(5, (14, 15)), (30, (14, 45)), (60, (15, 15))])
def test_a_card_moved_to_14_08_fills_the_same_day(minutes, mark):
    assert clock(minutes).due(ist(THU, 14, 8), ENTRY) == DueMark(THU, ist(THU, *mark))


def test_a_friday_card_fills_on_monday():
    assert clock(60).due(ist(FRI, 15, 16), ENTRY) == DueMark(MON, ist(MON, 10, 15))


def test_a_holiday_is_skipped():
    assert clock(60).due(ist(MON, 15, 16), ENTRY) == DueMark(WED, ist(WED, 10, 15))


def test_a_muhurat_only_day_is_skipped():
    friday, monday = date(2026, 11, 6), date(2026, 11, 9)  # Sun 8 Nov is the muhurat session
    assert clock(60).due(ist(friday, 15, 16), ENTRY) == DueMark(monday, ist(monday, 10, 15))


def test_an_away_session_moves_the_fill_one_session():
    assert clock(60, AwayDays(FRI)).due(ist(THU, 15, 16), ENTRY) == DueMark(MON, ist(MON, 10, 15), 1)


def test_an_entry_moved_onto_a_second_away_session_misses():
    assert clock(60, AwayDays(FRI, MON)).due(ist(THU, 15, 16), ENTRY) == Missed(MISSED_OWNER_AWAY)


def test_an_exit_keeps_moving():
    assert clock(60, AwayDays(FRI, MON)).due(ist(THU, 15, 16), EXIT) == DueMark(WED, ist(WED, 10, 15), 2)


def test_e4s_view_fills_at_the_decision_days_execution_snapshot():
    assert ExecutionSnapshotClock(time(15, 15)).due(ist(THU, 15, 0), ENTRY) == DueMark(THU, ist(THU, 15, 15))
