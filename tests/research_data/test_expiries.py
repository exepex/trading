"""Monthly-expiry identity (story A5): decided as of each day from what NSE had listed by then, never later data."""

from datetime import date

from fno.research_data.expiries import eligible_monthly, monthly_as_of, monthly_expiries

JAN_2_LISTED = [date(2024, 1, 4), date(2024, 1, 11), date(2024, 1, 18), date(2024, 1, 25), date(2024, 2, 1),
                date(2024, 2, 29), date(2024, 3, 28)]  # fmt: skip


def test_a_real_monthly_a_holiday_moved_monthly_and_an_expiry_change_are_decided_as_of_the_day():
    assert eligible_monthly(date(2024, 1, 15), monthly_expiries(set(JAN_2_LISTED))) == date(2024, 2, 29)  # 45 days
    moved = {date(2024, 3, 20), date(2024, 3, 27)}  # the month's last Thursday was a holiday: Wednesday expiry
    assert monthly_expiries(moved) == {date(2024, 3, 27)}
    before_change, after_change = {date(2025, 4, 24)}, {date(2025, 4, 24), date(2025, 4, 29)}
    assert monthly_expiries(before_change) == {date(2025, 4, 24)}  # each day uses only what it lists
    assert monthly_expiries(after_change) == {date(2025, 4, 29)}


def test_a_holiday_moved_weekly_is_not_mistaken_for_the_monthly():
    listings = {
        date(2025, 2, 20): {date(2025, 4, 24): 63},  # the April monthly is listed two months ahead
        date(2025, 3, 27): {date(2025, 4, 24): 28, date(2025, 4, 30): 34},  # the 30 Apr weekly appears in April
    }
    assert monthly_as_of(listings)[date(2025, 3, 27)] == {date(2025, 4, 24)}


def test_a_re_dated_monthly_keeps_only_its_new_date():
    listings = {
        date(2025, 7, 1): {date(2025, 9, 25): 86},  # listed for Thursday 25 Sep
        date(2025, 8, 1): {date(2025, 9, 30): 60},  # NSE moved it to Tuesday 30 Sep; the old date is gone
        date(2025, 8, 18): {date(2025, 9, 30): 43, date(2025, 8, 26): 8},
    }
    monthly = monthly_as_of(listings)
    assert monthly[date(2025, 8, 18)] == {date(2025, 9, 30)}
    assert eligible_monthly(date(2025, 8, 18), monthly[date(2025, 8, 18)]) == date(2025, 9, 30)


def test_future_listings_never_change_an_earlier_day():
    listings = {
        date(2025, 2, 20): {date(2025, 4, 24): 63},
        date(2025, 3, 27): {date(2025, 4, 24): 28, date(2025, 4, 30): 34},
    }
    before = monthly_as_of(listings)
    later = dict(listings)
    later[date(2025, 4, 1)] = {date(2025, 4, 30): 29, date(2025, 6, 26): 86, date(2025, 4, 24): 23}
    later[date(2025, 5, 2)] = {date(2025, 6, 26): 55, date(2025, 5, 29): 27}
    after = monthly_as_of(later)
    assert all(after[day] == before[day] for day in before)  # adding the future changes no past classification
