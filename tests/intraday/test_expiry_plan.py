"""Story A16 criterion 4: which two chains (nearest listed and nearest monthly by A5's rule, as A4) and the late
December fallback to NSE's listing."""

from datetime import date

import pytest

from fno.intraday.expiry_plan import ExpiryPlan, ExpiryPlanError
from fno.quotes.expiry_listing import ListedExpiries
from fno.quotes.recorder import POINT_IN_TIME_RULE

DAY = date(2026, 10, 15)


class Listing(ListedExpiries):
    def __init__(self, expiries):
        self.expiries = expiries

    def listed(self, underlying, today):
        return self.expiries, {"file": "nse"}


class Monthlies:
    def __init__(self, found=None, error=None):
        self.found, self.error = found, error

    def monthlies(self, underlying, listed, today):
        if self.error:
            raise self.error
        return self.found, []


def test_the_nearest_weekly_and_the_nearest_monthly():
    plan = ExpiryPlan(lambda: [date(2026, 10, 13), date(2026, 10, 19), date(2026, 10, 27), date(2026, 11, 3)])
    found = plan.plan(DAY)
    assert (found.nearest, found.monthly, found.chains) == (date(2026, 10, 19), date(2026, 10, 27),
                                                            (date(2026, 10, 19), date(2026, 10, 27)))  # fmt: skip
    assert found.check["status"] == "unverified"  # no NSE history wired in this test


def test_a_verified_monthly_by_the_point_in_time_rule():
    plan = ExpiryPlan(lambda: [date(2026, 10, 19), date(2026, 10, 27)], monthlies=Monthlies({date(2026, 10, 27)}))
    assert plan.plan(DAY).check == {"status": "verified", "rule": POINT_IN_TIME_RULE}


def test_an_unreadable_history_falls_back_to_the_last_of_month_rule_and_says_why():
    plan = ExpiryPlan(lambda: [date(2026, 10, 19), date(2026, 10, 27)], monthlies=Monthlies(error=OSError("x")))
    found = plan.plan(DAY)
    assert found.monthly == date(2026, 10, 27) and found.check["reason"] == "history unreadable: OSError"


def test_late_december_uses_nse_listing_when_groww_lists_nothing_ahead():
    plan = ExpiryPlan(lambda: [date(2026, 12, 29)], Listing([date(2027, 1, 5), date(2027, 1, 26)]))
    found = plan.plan(date(2026, 12, 30))
    assert found.chains == (date(2027, 1, 5), date(2027, 1, 26))


def test_only_one_listed_expiry_records_one_chain():
    found = ExpiryPlan(lambda: [date(2026, 10, 27)]).plan(DAY)
    assert found.chains == (date(2026, 10, 27),)


@pytest.mark.parametrize("fallback", [None, Listing([])])
def test_no_listed_expiry_is_refused(fallback):
    with pytest.raises(ExpiryPlanError):
        ExpiryPlan(lambda: [], fallback).plan(DAY)


def test_late_december_merges_nse_listing_for_the_second_chain():
    plan = ExpiryPlan(lambda: [date(2026, 12, 29)], Listing([date(2027, 1, 5), date(2027, 1, 26)]))
    found = plan.plan(date(2026, 12, 23))
    assert found.chains == (date(2026, 12, 29), date(2027, 1, 5))


def test_a_failed_broker_list_falls_back_to_nse_and_says_so():
    def refused():
        raise RuntimeError("Year cannot be in the future")

    found = ExpiryPlan(refused, Listing([date(2026, 10, 19), date(2026, 10, 27)])).plan(DAY)
    assert found.chains == (date(2026, 10, 19), date(2026, 10, 27))
    assert found.check["broker_list"] == "failed: RuntimeError"
