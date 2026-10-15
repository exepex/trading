"""Story F9a criterion 5, the declared cost split, by hand. November 2026: plan Rs 20,000; book 2 used 30 minutes on
2 Nov and 10 on 3 Nov, development 60: book 2's share is 20,000 x 40/100 = Rs 8,000 (F8). 2 Nov: 8,000 x 30/40 =
Rs 6,000, three units consulted: Rs 2,000 each. 3 Nov: Rs 2,000 = 200,000 paise over three units: 66,666 each and the
2 paise left to the first, macro: 66,668. Macro's operating cost: (200,000 + 66,668) / 2 = 133,334 paise."""

from datetime import date

from fno.budget.allocation import allocate
from fno.role_value.cost import ConsultedDay, book_day_paise, daily_parts, mean_cost, split_paise
from tests.role_value.builders import BOOK, usage

D1, D2 = date(2026, 11, 2), date(2026, 11, 3)
UNITS = ("macro", "positioning", "vol")
USAGE = [usage(D1, "30.00"), usage(D2, "10.00"), usage(D1, "60.00", book="", purpose="development")]
DAYS = [ConsultedDay(D1, UNITS), ConsultedDay(D2, UNITS)]


def cost(unit, plan=20_000.0, rows=USAGE, days=DAYS):
    """The unit's operating cost: the mean of its daily parts over every consulted day."""
    return mean_cost(
        daily_parts(unit, days, BOOK, lambda month: allocate(month, plan, rows), lambda month: rows).values()
    )


def test_the_book_s_daily_cost_follows_its_minutes():
    allocation = allocate("2026-11", 20_000.0, USAGE)
    assert book_day_paise(allocation, USAGE, BOOK, D1) == 600_000
    assert book_day_paise(allocation, USAGE, BOOK, D2) == 200_000


def test_the_split_sums_exactly_and_the_remainder_goes_to_the_first_unit():
    parts = split_paise(200_000, ("vol", "macro", "positioning"))
    assert parts == {"macro": 66_668, "positioning": 66_666, "vol": 66_666} and sum(parts.values()) == 200_000


def test_a_unit_s_cost_is_the_mean_of_its_parts_over_every_consulted_day():
    assert cost("macro") == 1333.34
    assert cost("vol") == 1333.33


def test_a_day_the_unit_was_not_consulted_carries_no_part():
    days = [ConsultedDay(D1, UNITS), ConsultedDay(D2, ("macro", "vol"))]
    assert cost("positioning", days=days) == 2000.0
    assert cost("macro", days=days) == 1500.0  # (2,000 + 1,000) / 2


def test_no_plan_cost_or_a_consulted_day_without_usage_is_unknown_never_zero():
    assert cost("macro", plan=None) is None
    assert cost("macro", rows=[usage(D1, "30.00")]) is None  # 3 Nov consulted, no usage row


def test_each_day_keeps_its_own_part():
    parts = daily_parts("macro", DAYS, BOOK, lambda month: allocate(month, 20_000.0, USAGE), lambda month: USAGE)
    assert parts == {D1: 2000.0, D2: 666.68}
