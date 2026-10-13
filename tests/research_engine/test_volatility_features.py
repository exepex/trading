"""F1 and F2 on small hand-built panels (story B1 criteria 2 and 3)."""

import math
from datetime import date

import pytest
from feature_fixtures import (
    EXPIRY,
    black76,
    chain,
    context,
    data,
    future,
    make_panel,
    session_days,
    zigzag_closes,
)

from fno.constants import SESSION_MUHURAT
from fno.research_data.panel_reader import SessionClose
from fno.research_engine.implied_vol import Black76
from fno.research_engine.volatility_features import AtmIvMinusRealised, VixAboveMedian, atm_strike

DAYS = session_days(21)
DAY = DAYS[-1]  # 21 Jan 2025: 65 calendar days to the 27 Mar 2025 expiry
YEARS = (EXPIRY - DAY).days / 365
SPOT, FORWARD = 20000.0, 20100.0  # zigzag closes end at 20000
CALL_VOL, PUT_VOL = 0.18, 0.16
F1 = AtmIvMinusRealised(Black76(), 0.065)


def f1_panel(closes=None, prices=None, legs_volume=100, future_volume=100, strikes=(19900.0, 20000.0, 20100.0)):
    prices = prices or {
        (SPOT, "CE"): black76(FORWARD, SPOT, YEARS, CALL_VOL, "CE"),
        (SPOT, "PE"): black76(FORWARD, SPOT, YEARS, PUT_VOL, "PE"),
    }
    closes = closes if closes is not None else zigzag_closes(21)
    days = DAYS[-len(closes) :]
    options = {DAY: chain(list(strikes), prices, volume=legs_volume)}
    return make_panel(days, closes, options=options, futures={DAY: [future(FORWARD, future_volume)]})


def f1(panel, day=DAY):
    return F1.value(data(panel), day, context(DAYS[-1], DAYS[-1]))


def test_f1_equals_the_hand_calculation():
    """ATM IV = (18 + 16) / 2 = 17 points; realised = 0.01 x sqrt(252) = 15.87 points; F1 = 1.13."""
    realised = 0.01 * math.sqrt(252) * 100
    assert f1(f1_panel()) == pytest.approx(17.0 - realised, abs=0.01)
    assert f1(f1_panel()) == pytest.approx(1.1255, abs=0.0001)


def test_atm_is_the_nearest_listed_strike_and_the_lower_one_on_a_tie():
    quotes = chain([19950.0, 20050.0, 20100.0], {})
    assert atm_strike(quotes, 20000.0) == 19950.0  # equal distance: the lower strike
    assert atm_strike(quotes, 20001.0) == 20050.0
    assert atm_strike([], 20000.0) is None


def test_on_a_tie_f1_prices_the_lower_strike():
    tied = {**{(19950.0, k): black76(FORWARD, 19950.0, YEARS, 0.17, k) for k in ("CE", "PE")}}
    panel = f1_panel(prices=tied, strikes=(19950.0, 20050.0))
    assert f1(panel) == pytest.approx(17.0 - 0.01 * math.sqrt(252) * 100, abs=0.01)


def _without(panel, kind):
    quotes = tuple(q for q in panel.options[DAY] if not (q.strike == SPOT and q.kind == kind))
    return make_panel(DAYS, zigzag_closes(21), options={DAY: quotes}, futures=panel.futures)


def _untraded(panel, kind):
    quotes = tuple(q._replace(volume=0) if q.strike == SPOT and q.kind == kind else q for q in panel.options[DAY])
    return make_panel(DAYS, zigzag_closes(21), options={DAY: quotes}, futures=panel.futures)


@pytest.mark.parametrize("kind", ["CE", "PE"])
def test_f1_is_none_for_a_missing_or_untraded_atm_leg(kind):
    assert f1(_without(f1_panel(), kind)) is None
    assert f1(_untraded(f1_panel(), kind)) is None


@pytest.mark.parametrize(
    "call_price",
    [
        25000.0,  # above the discounted forward: no volatility gives it
        black76(FORWARD, SPOT, YEARS, 2.5, "CE"),  # needs 250%: above the 200% bound
        black76(FORWARD, SPOT, YEARS, 0.005, "CE"),  # needs 0.5%: below the 1% bound
    ],
)
def test_f1_is_none_when_the_solver_fails_or_hits_a_bound(call_price):
    prices = {(SPOT, "CE"): call_price, (SPOT, "PE"): black76(FORWARD, SPOT, YEARS, PUT_VOL, "PE")}
    assert f1(f1_panel(prices=prices)) is None


def test_f1_is_none_with_fewer_than_21_valid_closes():
    assert f1(f1_panel(closes=zigzag_closes(20))) is None
    gap = zigzag_closes(21)
    gap[5] = None  # a session the panel left out (2021-03-30 style)
    assert f1(f1_panel(closes=gap)) is None


def test_f1_is_none_without_a_traded_same_expiry_future():
    assert f1(f1_panel(future_volume=0)) is None
    panel = f1_panel()
    assert f1(make_panel(DAYS, zigzag_closes(21), options=panel.options)) is None


def test_f1_and_f2_are_none_on_a_day_that_is_not_a_daily_session():
    panel = f1_panel()
    assert f1(panel, date(2025, 1, 22)) is None  # after the last session
    muhurat = panel.sessions[:-1] + (SessionClose(DAY, SESSION_MUHURAT, SPOT, 15.0),)
    panel = type(panel)(muhurat, panel.options, panel.futures)
    assert f1(panel) is None
    assert VixAboveMedian().value(data(panel), DAY, context(DAY, DAY)) is None


def f2(previous_vix, today_vix):
    days = session_days(len(previous_vix) + 1)
    panel = make_panel(days, [20000.0] * len(days), vix=[*previous_vix, today_vix])
    return VixAboveMedian().value(data(panel), days[-1], context(days[-1], days[-1]))


def test_f2_compares_with_the_median_of_the_previous_250_closes():
    history = [float(v) for v in range(1, 251)]  # median 125.5
    assert f2(history, 126.0) is True
    assert f2(history, 125.0) is False
    assert f2(history, 125.5) is False  # not above
    assert f2([1000.0] + history, 126.0) is True  # only the last 250 count


def test_f2_is_none_with_fewer_than_250_valid_previous_closes():
    history = [float(v) for v in range(1, 251)]
    assert f2(history[1:], 300.0) is None
    assert f2([None, *history[1:]], 300.0) is None
    assert f2([5.0, None, *history[1:]], 300.0) is True  # a left-out session is skipped, not counted
    assert f2(history, None) is None
