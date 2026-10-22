"""The spread buckets, model and learner (MS-SIM-b, 7.2)."""

from dataclasses import replace
from datetime import date, timedelta

import pytest

from fno.school.constants import OptionKind, RoadCode
from fno.school.contracts.snapshot import ContractKey, SlotQuote
from fno.school.simulator.constants import MIN_QUOTED_SESSIONS
from fno.school.simulator.spreads.bucket import DaysToExpiry, Moneyness, SpreadBucket, bucket_of
from fno.school.simulator.spreads.learner import SpreadLearner, relative_half_spread
from fno.school.simulator.spreads.model import (
    InsufficientSpreadData,
    Scenario,
    SpreadModel,
    SpreadScenarios,
    percentile,
)
from tests.school.contracts import builders as b

DAY0 = date(2026, 10, 1)
BUCKET = SpreadBucket("BANKNIFTY", Moneyness.NEAR, DaysToExpiry.CYCLE)


def snap(code=RoadCode.BANKNIFTY_MONTHLY, session=DAY0, quotes=None, spot=1000.0, days=30):
    expiry = session + timedelta(days=days)
    quotes = quotes if quotes is not None else {ContractKey(expiry, 1000.0, OptionKind.CALL): b.quote(99.0, 101.0)}
    return replace(b.snapshot(code, quotes), session=session, spot=spot, expiries=(expiry,))


def quotes_at(spreads: list[float], days=30, session=DAY0, strike=1000.0):
    """One call per strike step, each with the given gap around a mid of 100."""
    expiry = session + timedelta(days=days)
    return {
        ContractKey(expiry, strike + n * 0.01, OptionKind.CALL): b.quote(100 - g / 2, 100 + g / 2)
        for n, g in enumerate(spreads)
    }


# ---- buckets -------------------------------------------------------------------------------------------------------


MONEYNESS_CASES = [
    (1009.9, Moneyness.NEAR), (1010.0, Moneyness.MID), (1019.9, Moneyness.MID),
    (1020.0, Moneyness.FAR), (1040.0, Moneyness.DEEP), (960.0, Moneyness.DEEP),
]  # fmt: skip
DTE_CASES = [
    (0, DaysToExpiry.WEEK), (7, DaysToExpiry.WEEK), (8, DaysToExpiry.MONTH), (21, DaysToExpiry.MONTH),
    (22, DaysToExpiry.CYCLE), (45, DaysToExpiry.CYCLE), (46, DaysToExpiry.LONG),
]  # fmt: skip


@pytest.mark.parametrize(("strike", "band"), MONEYNESS_CASES)
def test_the_moneyness_band_edges(strike, band):
    assert bucket_of("X", 1000.0, strike, DAY0, DAY0 + timedelta(days=30)).moneyness is band


@pytest.mark.parametrize(("days", "band"), DTE_CASES)
def test_the_days_to_expiry_band_edges(days, band):
    assert bucket_of("X", 1000.0, 1000.0, DAY0, DAY0 + timedelta(days=days)).dte is band


def test_an_expired_contract_or_a_spot_that_is_not_a_price_has_no_bucket():
    assert bucket_of("X", 1000.0, 1000.0, DAY0, DAY0 - timedelta(days=1)) is None
    assert bucket_of("X", 0.0, 1000.0, DAY0, DAY0 + timedelta(days=5)) is None


# ---- the model -----------------------------------------------------------------------------------------------------


def model_of(n: int) -> SpreadModel:
    return SpreadModel({BUCKET: {DAY0 + timedelta(days=i): 0.001 * (i + 1) for i in range(n)}})


def test_29_quoted_sessions_are_insufficient_and_30_give_three_scenarios():
    assert MIN_QUOTED_SESSIONS == 30
    short = model_of(29).scenarios(BUCKET)
    assert isinstance(short, InsufficientSpreadData) and short.sessions == 29
    assert "insufficient spread data" in str(short) and "29 of 30" in str(short)
    enough = model_of(30).scenarios(BUCKET)
    assert isinstance(enough, SpreadScenarios) and enough.sessions == 30
    assert set(enough.half_spreads) == {Scenario.MEDIAN, Scenario.P75, Scenario.P95}


def test_the_scenarios_are_the_median_75th_and_95th_percentile_of_the_session_values():
    found = model_of(30).scenarios(BUCKET)  # values 0.001 ... 0.030
    assert found.half_spread(Scenario.MEDIAN) == pytest.approx(0.0155)
    assert found.half_spread(Scenario.P75) == pytest.approx(0.02275)  # position 0.75 * 29 = 21.75 between 22nd and 23rd
    assert found.half_spread(Scenario.P95) == pytest.approx(0.02855)  # position 27.55
    assert found.half_spread(Scenario.MEDIAN) < found.half_spread(Scenario.P75) < found.half_spread(Scenario.P95)


def test_an_unknown_bucket_is_insufficient_never_borrowed_from_another():
    other = SpreadBucket("NIFTY", Moneyness.NEAR, DaysToExpiry.CYCLE)
    found = model_of(40).scenarios(other)
    assert isinstance(found, InsufficientSpreadData) and found.sessions == 0


def test_percentile_of_one_value_and_of_two():
    assert percentile([0.5], 0.95) == 0.5
    assert percentile([1.0, 3.0], 0.5) == 2.0


# ---- the learner ---------------------------------------------------------------------------------------------------


def test_a_quote_is_its_half_gap_over_the_mid_floored_at_half_a_tick():
    assert relative_half_spread(b.quote(99.0, 101.0)) == pytest.approx(0.01)
    assert relative_half_spread(b.quote(1.00, 1.01)) == pytest.approx(
        0.025 / 1.005
    )  # one tick wide or less: half a tick


def test_a_one_sided_invalid_or_crossed_quote_gives_no_value():
    assert relative_half_spread(SlotQuote(None, 5.0, None, 10, None, True)) is None
    assert relative_half_spread(replace(b.quote(), valid=False)) is None
    assert relative_half_spread(b.quote(101.0, 99.0)) is None


def test_a_session_counts_once_however_many_strikes_and_a_big_session_does_not_dominate():
    big = snap(session=DAY0, quotes=quotes_at([40.0] * 200))  # 200 quotes of a 20% half gap
    rest = [
        snap(session=DAY0 + timedelta(days=i), quotes=quotes_at([2.0], session=DAY0 + timedelta(days=i)))
        for i in range(1, 30)
    ]  # 29 sessions of 1%
    model = SpreadLearner().learn([big, *rest])
    assert model.sessions(BUCKET) == 30
    found = model.scenarios(BUCKET)
    assert found.half_spread(Scenario.MEDIAN) == pytest.approx(0.01)  # one big session moves the median not at all
    assert found.half_spread(Scenario.P75) == pytest.approx(0.01)


def test_a_session_value_is_the_median_of_its_quotes():
    model = SpreadLearner().learn([snap(quotes=quotes_at([2.0, 4.0, 100.0]))])
    assert model.by_session[BUCKET][DAY0] == pytest.approx(0.02)


def test_two_roads_of_one_underlying_on_one_day_count_as_one_session():
    monthly = snap(RoadCode.NIFTY_MONTHLY, quotes=quotes_at([2.0]))
    weekly = snap(RoadCode.NIFTY_WEEKLY, quotes=quotes_at([6.0]))
    model = SpreadLearner().learn([monthly, weekly])
    nifty = SpreadBucket("NIFTY", Moneyness.NEAR, DaysToExpiry.CYCLE)
    assert model.sessions(nifty) == 1 and model.by_session[nifty][DAY0] == pytest.approx(0.02)


def test_an_all_one_sided_bucket_and_an_empty_input_are_insufficient():
    one_sided = {
        ContractKey(DAY0 + timedelta(days=30), 1000.0, OptionKind.CALL): SlotQuote(None, 5.0, None, 10, None, True)
    }
    assert SpreadLearner().learn([snap(quotes=one_sided)]).sessions(BUCKET) == 0
    assert isinstance(SpreadLearner().learn([]).scenarios(BUCKET), InsufficientSpreadData)


def test_buckets_are_kept_apart_by_underlying_moneyness_and_days():
    quotes = {**quotes_at([2.0], days=30), **quotes_at([4.0], days=5, strike=1030.0)}
    model = SpreadLearner().learn([snap(quotes=quotes)])
    assert model.sessions(BUCKET) == 1
    assert model.sessions(SpreadBucket("BANKNIFTY", Moneyness.FAR, DaysToExpiry.WEEK)) == 1
