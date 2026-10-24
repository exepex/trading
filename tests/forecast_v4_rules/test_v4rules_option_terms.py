"""Story G7b completion, criteria 6 and 9: V5's and V4's pack-frozen terms and the live-quote rule (W5), on fixture
packs priced by Black-76, the committed NSE calendar and v4_golden.json."""

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

from fno.forecast_v4.units import v4_outcome
from fno.forecast_v4_rules.live_quotes import NO_QUOTE, NO_TRADE_TODAY, SPREAD, TwoSided, quote_problem
from fno.forecast_v4_rules.option_terms import (
    EXPIRY_LIST_UNAVAILABLE,
    FUTURE_NOT_MONTHLY,
    IV_UNSOLVED,
    NO_FUTURE_QUOTE,
    NO_V4_EXPIRY,
    PAST_CALENDAR,
    V4_EXPIRY_MISMATCH,
    OptionTerms,
    OptionTermsRule,
    Void,
    atm_strike,
)
from fno.models import IST
from fno.research_data.calendar import load_session_calendar
from fno.research_engine.implied_vol import Black76
from tests.forecast_v4_rules.option_fixtures import LISTED, MONTHLY, RATE, TRADED, WEEKLY, D, chain, replace

ROOT = Path(__file__).resolve().parents[2]
CALENDAR = load_session_calendar(ROOT / "research" / "data" / "calendar" / "nse_sessions.csv")
GOLDEN = json.loads((ROOT / "tests" / "fixtures" / "forecast_v4" / "v4_golden.json").read_text())
RULE = OptionTermsRule(Black76(), RATE, CALENDAR)
SPOT, FORWARD = 26010.0, 26080.0
FUTURE = TwoSided(26075.0, 26085.0, TRADED)  # mid 26080


def test_live_quote_rule_boundaries():
    assert quote_problem(TwoSided(97.5, 102.5, TRADED), D) == ""  # exactly 5% of the mid passes
    assert quote_problem(TwoSided(7.02, 7.38, TRADED), D) == ""  # exactly 5% too (0.05000000000000005 in floats)
    assert quote_problem(TwoSided(23.40, 24.60, TRADED), D) == ""
    assert quote_problem(TwoSided(97.495, 102.505, TRADED), D) == SPREAD  # 5.01%
    assert quote_problem(TwoSided(None, 102.5, TRADED), D) == NO_QUOTE
    assert quote_problem(TwoSided(0.0, 1.0, TRADED), D) == NO_QUOTE
    assert quote_problem(TwoSided(101.0, 100.0, TRADED), D) == NO_QUOTE  # crossed
    assert quote_problem(TwoSided(100.0, 100.0, TRADED), D) == ""  # locked: ask equals bid
    assert quote_problem(TwoSided(99.0, 101.0, TRADED - timedelta(days=1)), D) == NO_TRADE_TODAY
    assert quote_problem(TwoSided(99.0, 101.0, None), D) == NO_TRADE_TODAY  # Groww with no last trade
    assert quote_problem(TwoSided(99.0, 101.0, None, traded_flag=True), D) == ""  # a volume-only source


def test_atm_strike_is_nearest_spot_with_a_tie_to_the_lower():
    quotes = chain(WEEKLY, FORWARD, 0.14)
    assert atm_strike(quotes, 26049.0) == 26000.0
    assert atm_strike(quotes, 26050.0) == 26000.0  # tie: lower
    assert atm_strike(quotes, 26051.0) == 26100.0
    assert atm_strike([], 26000.0) is None


def test_v4_recovers_the_parity_forward_and_iv_and_reproduces_the_golden_example():
    terms = RULE.v4(D, SPOT, chain(WEEKLY, FORWARD, 0.138), WEEKLY)
    assert isinstance(terms, OptionTerms)
    assert (terms.expiry, terms.strike, terms.sessions, terms.calendar_days) == (WEEKLY, 26000.0, 5, 7)
    assert terms.forward == pytest.approx(FORWARD, rel=1e-9) and terms.iv == pytest.approx(0.138, abs=1e-8)
    case = GOLDEN["cases"][0]  # 7 calendar days, 5 sessions
    assert terms.sigma_iv_session_clock == pytest.approx(case["implied_vol_252"], abs=1e-7)
    assert v4_outcome(GOLDEN["session_variances"], terms.iv, terms.calendar_days, terms.sessions) is case["outcome"]


def test_v4_voids_without_its_expiry_and_never_takes_another():
    quotes = chain(MONTHLY, FORWARD, 0.14) + chain(WEEKLY, FORWARD, 0.14)
    assert RULE.v4(D, SPOT, quotes, None) == Void(D, NO_V4_EXPIRY)
    # the monthly is present, the weekly v4_expiry's quotes are not: void, never the monthly
    assert RULE.v4(D, SPOT, chain(MONTHLY, FORWARD, 0.14), WEEKLY) == Void(D, NO_V4_EXPIRY)
    assert RULE.v4(D, SPOT, replace(quotes, 26000.0, "PE", expiry=MONTHLY), WEEKLY) == Void(D, NO_V4_EXPIRY)
    # a v4_expiry with 4 scored sessions (Wed 28 Oct -> 3 Nov) is refused, not trusted
    assert RULE.v4(date(2026, 10, 28), SPOT, quotes, WEEKLY) == Void(date(2026, 10, 28), V4_EXPIRY_MISMATCH)


def test_v4_voids_on_a_leg_that_is_wide_stale_or_unsolvable():
    quotes = chain(WEEKLY, FORWARD, 0.14)
    assert RULE.v4(D, SPOT, replace(quotes, 26000.0, "CE", ask=10_000.0), WEEKLY).reason == SPREAD
    stale = TRADED - timedelta(days=1)
    assert RULE.v4(D, SPOT, replace(quotes, 26000.0, "PE", last_trade_time=stale), WEEKLY).reason == NO_TRADE_TODAY
    # parity makes both legs agree, so a solvable pair always solves; a put above the strike gives F <= 0: no IV
    absurd = replace(quotes, 26000.0, "PE", bid=30_000.0, ask=30_100.0)
    assert RULE.v4(D, SPOT, absurd, WEEKLY).reason == IV_UNSOLVED


def test_v5_terms_from_the_next_monthly_with_the_futures_mid():
    terms = RULE.v5(D, SPOT, chain(MONTHLY, FORWARD, 0.14), MONTHLY, FUTURE, LISTED)
    assert isinstance(terms, OptionTerms)
    assert (terms.expiry, terms.strike, terms.forward) == (MONTHLY, 26000.0, 26080.0)
    assert (terms.sessions, terms.calendar_days) == (18, 27)  # 28 Oct - 23 Nov: 10 Nov a holiday, the 8 Nov muhurat out
    assert terms.iv == pytest.approx(0.14, abs=1e-8)
    assert terms.premium == pytest.approx(terms.call_mid + terms.put_mid)


def test_v5_checks_the_packs_future_against_nse_s_listed_monthlies():
    quotes = chain(MONTHLY, FORWARD, 0.14)
    assert RULE.v5(D, SPOT, quotes, WEEKLY, FUTURE, LISTED) == Void(D, FUTURE_NOT_MONTHLY)  # a weekly
    assert RULE.v5(D, SPOT, quotes, D, FUTURE, LISTED) == Void(D, FUTURE_NOT_MONTHLY)  # expiring on d itself
    assert RULE.v5(D, SPOT, quotes, MONTHLY, FUTURE, None) == Void(D, EXPIRY_LIST_UNAVAILABLE)
    assert RULE.v5(D, SPOT, quotes, MONTHLY, FUTURE, []) == Void(D, FUTURE_NOT_MONTHLY)


def test_v5_voids_on_the_future_quote():
    quotes = chain(MONTHLY, FORWARD, 0.14)
    assert RULE.v5(D, SPOT, quotes, MONTHLY, None, LISTED) == Void(D, NO_FUTURE_QUOTE)
    assert RULE.v5(D, SPOT, quotes, MONTHLY, TwoSided(None, None, TRADED), LISTED) == Void(D, NO_FUTURE_QUOTE)
    # the future did not trade today (judge 578.1 n1: W5 is never relaxed for the future)
    assert RULE.v5(D, SPOT, quotes, MONTHLY, TwoSided(26075.0, 26085.0, None), LISTED) == Void(D, NO_TRADE_TODAY)
    assert RULE.v5(D, SPOT, [], MONTHLY, FUTURE, LISTED) == Void(D, NO_QUOTE)


def test_a_last_trade_before_the_day_in_ist_is_not_today():
    late_yesterday = datetime.combine(D - timedelta(days=1), time(15, 29), IST)
    assert quote_problem(TwoSided(99.0, 101.0, late_yesterday), D) == NO_TRADE_TODAY


def test_v5_voids_on_a_stale_leg():
    stale = replace(chain(MONTHLY, FORWARD, 0.14), 26000.0, "CE", last_trade_time=TRADED - timedelta(days=1))
    assert RULE.v5(D, SPOT, stale, MONTHLY, FUTURE, LISTED) == Void(D, NO_TRADE_TODAY)


def test_an_expiry_past_the_calendar_voids_never_raises():
    if CALENDAR.last.year != 2026:
        pytest.skip("the calendar now covers 2027")
    day, january = date(2026, 12, 29), date(2027, 1, 26)
    traded = datetime.combine(day, time(14, 29), IST)
    quotes, future = chain(january, FORWARD, 0.14, traded=traded), TwoSided(26075.0, 26085.0, traded)
    assert RULE.v5(day, SPOT, quotes, january, future, [day, january]) == Void(day, PAST_CALENDAR)
    assert RULE.v4(day, SPOT, quotes, january) == Void(day, PAST_CALENDAR)
