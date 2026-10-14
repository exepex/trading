"""Which (version, expiry) is an opportunity today: the first trading day the monthly expiry is 30-45 days away, with
the exit at the last trading day at least 21 days before it (experiment 1's decision day)."""

from datetime import date, timedelta

from fno.composition import build_session_calendar
from fno.playbook.opportunities import OpportunityFinder
from fno.research_engine.cycles import TradingDays

from .evaluation_builders import strategy

FINDER = OpportunityFinder(TradingDays(build_session_calendar()))
TUESDAY = date(2026, 10, 13)


def find(day, expiries):
    return FINDER.find(strategy("sc-a"), day, expiries, "book")


def test_the_first_session_inside_the_window_is_the_opportunity():
    expiry = TUESDAY + timedelta(days=45)
    [opportunity] = find(TUESDAY, [expiry])
    assert opportunity.context.entry_day == TUESDAY and opportunity.context.expiry == expiry
    assert opportunity.context.exit_day == date(2026, 11, 6)  # last session on or before expiry - 21 days
    assert opportunity.opportunity_id == f"sc-a-v1:{expiry.isoformat()}"


def test_later_sessions_in_the_window_are_not_new_opportunities():
    expiry = TUESDAY + timedelta(days=45)
    assert find(TUESDAY + timedelta(days=1), [expiry]) == []


def test_after_a_weekend_the_first_session_inside_counts():
    monday = date(2026, 10, 19)  # the Friday before was 46+ days away
    expiry = date(2026, 12, 2)  # 44 days after Monday, 47 after Friday 16 Oct
    assert [o.context.expiry for o in find(monday, [expiry])] == [expiry]


def test_expiries_outside_the_window_and_non_sessions_give_nothing():
    assert find(TUESDAY, [TUESDAY + timedelta(days=29), TUESDAY + timedelta(days=46)]) == []
    assert find(date(2026, 10, 17), [date(2026, 10, 17) + timedelta(days=40)]) == []  # a Saturday
