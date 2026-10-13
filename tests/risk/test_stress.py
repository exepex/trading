"""Story C2 criterion 4: the stress engine against hand computations with fixed prices, and the stress limit.

Setup: NIFTY 25,000; every option expires tomorrow, so after a scenario's one day each leg is worth its intrinsic value
and every loss can be checked by hand. Open: a short iron fly 25,000 with 200-point wings, 1 lot (65 units), cash flow
so far Rs 8,000. Proposed: a short condor 25,500/24,500 with 200-point wings, entry at mids without pads or charges
(credit 20 + 25 - 6 - 8 = 31 points, Rs 2,015 a lot).
"""

import math
from datetime import date, timedelta

import pytest

from fno.analytics import bs_price
from fno.constants import OPTION_CALL
from fno.research_engine.structures import BOUGHT
from fno.risk.rules import StressLoss
from fno.risk.settings import Scenario
from fno.risk.stress import Shock, StressEngine, stress_positions
from fno.risk.trade_costs import SimulatorTradeCosts

from .builders import (
    CHARGES,
    CONDOR,
    DAY,
    FLY,
    LOT,
    MODEL,
    ZERO_CHARGES,
    book,
    market,
    open_trade,
    proposal,
    short_condor,
    short_fly,
)

EXPIRY = DAY + timedelta(days=1)
PRICES = {
    (25000, "CE"): 60.0,
    (25000, "PE"): 55.0,
    (25200, "CE"): 5.0,
    (24800, "PE"): 4.0,  # the open fly
    (25500, "CE"): 20.0,
    (24500, "PE"): 25.0,
    (25700, "CE"): 6.0,
    (24300, "PE"): 8.0,  # the proposed condor
}
FLY_MARKED = (-60 - 55 + 5 + 4) * LOT  # -6,890: the fly's marked value (short legs count minus)
CONDOR_CREDIT = 31 * LOT  # 2,015
SCENARIOS = (
    Scenario("nifty_down_8pct", -8, 1),
    Scenario("nifty_up_5pct", 5, 1),
    Scenario("iv_double", 0, 2),
    Scenario("replay_2026-02-01", -1.9557, 1.1079),
    Scenario("replay_2026-02-03", 2.5476, 0.9301),
)
# Hand computation, per scenario: (fly value, condor value) per unit at expiry, from intrinsic values.
#   -8%: NIFTY 23,000. Fly: -2,000 (25,000 put) + 1,800 (24,800 put) = -200. Condor: -1,500 + 1,300 = -200.
#   +5%: NIFTY 26,250. Fly: -1,250 + 1,050 = -200. Condor: -750 + 550 = -200.
#   IV x2, no move: every leg at 25,000 is worth 0 at expiry: fly 0, condor 0.
#   -1.9557%: NIFTY 24,511.075. Fly: -488.925 + 288.925 = -200. Condor: both puts out of the money: 0.
#   +2.5476%: NIFTY 25,636.90. Fly: -636.90 + 436.90 = -200. Condor: -136.90 (25,500 call), 25,700 call 0.
HAND_VALUES = {
    "nifty_down_8pct": (-200, -200),
    "nifty_up_5pct": (-200, -200),
    "iv_double": (0, 0),
    "replay_2026-02-01": (-200, 0),
    "replay_2026-02-03": (-200, -136.90),
}


def _setup(lots: int = 1):
    fly = open_trade("fly-1", FLY, 200, short_fly(25000, 200), EXPIRY, cash_flow=8000.0)
    condor = proposal("condor-1", CONDOR, 200, short_condor(25500, 24500, 200), EXPIRY, lots=lots)
    return condor, book([fly]), market(25000, PRICES, EXPIRY)  # in the order a rule checks them


def _results(lots: int = 1):
    condor, the_book, the_market = _setup(lots)
    costs = SimulatorTradeCosts(ZERO_CHARGES, pad=0.0)
    positions = stress_positions(the_book, condor, costs.entry_cash_flow(condor, the_market))
    return StressEngine(MODEL).run(positions, the_market, [Shock.of(s) for s in SCENARIOS])


def test_the_proposal_entry_cash_flow_is_its_credit_by_hand():
    condor, _, the_market = _setup()
    assert SimulatorTradeCosts(ZERO_CHARGES, pad=0.0).entry_cash_flow(condor, the_market) == pytest.approx(2015.0)


@pytest.mark.parametrize("result", _results(), ids=lambda r: r.shock.name)
def test_each_scenario_loss_equals_the_hand_computation(result):
    fly_value, condor_value = (v * LOT for v in HAND_VALUES[result.shock.name])
    fly, condor = result.trades
    assert fly.loss_from_marks == pytest.approx(FLY_MARKED - fly_value)
    assert fly.loss_from_entry == pytest.approx(-(8000.0 + fly_value))
    assert condor.loss_from_entry == pytest.approx(-(CONDOR_CREDIT + condor_value))
    assert condor.loss_from_marks == pytest.approx(-CONDOR_CREDIT - condor_value)  # mids = entry without pads
    assert result.counted_loss == pytest.approx(fly.loss_from_marks + condor.loss_from_entry)


def test_worked_numbers_of_the_down_8pct_scenario():
    down = _results()[0]
    assert down.trades[0].loss_from_marks == pytest.approx(6110.0)  # -6,890 - (-13,000)
    assert down.trades[0].loss_from_entry == pytest.approx(5000.0)  # -(8,000 - 13,000)
    assert down.trades[1].loss_from_entry == pytest.approx(10985.0)  # -(2,015 - 13,000)
    assert down.counted_loss == pytest.approx(17095.0)


def _stress_rule(limit: float) -> StressLoss:
    return StressLoss(StressEngine(MODEL), SimulatorTradeCosts(ZERO_CHARGES, pad=0.0), SCENARIOS, limit)


def test_one_lot_condor_passes_and_three_lots_are_blocked_above_30000():
    one = _stress_rule(30000).check(*_setup(lots=1))
    three = _stress_rule(30000).check(*_setup(lots=3))
    assert one.ok and one.numbers["worst_loss_rs"] == pytest.approx(17095.0)
    assert not three.ok and three.numbers["worst_loss_rs"] == pytest.approx(6110.0 + 3 * (13000 - 2015))  # 39,065
    assert "above Rs 30,000.00" in three.reason


@pytest.mark.parametrize(("limit", "ok"), [(17095.0, True), (17094.99, False)])
def test_stress_limit_just_inside_and_just_outside(limit, ok):
    assert _stress_rule(limit).check(*_setup()).ok is ok


def test_repricing_uses_black_76_on_the_future_with_the_iv_factor_and_one_day_of_decay():
    """A textbook value: Black-Scholes with spot 100, strike 100, 1 year, 5%, 20% volatility gives a call of 10.4506;
    Black-76 on the forward 100 x e^0.05 with the same rate must give the same. The quote's IV 10% is doubled and one
    of 366 days passes."""
    expiry = DAY + timedelta(days=366)
    the_market = market(100, {(100, OPTION_CALL): 9.0}, expiry, iv=0.10, forward=100 * math.exp(0.05), rate=0.05)
    held = open_trade("call", FLY, 100, [(100, OPTION_CALL, BOUGHT)], expiry, cash_flow=-9.0 * LOT)
    (result,) = StressEngine(MODEL).run(stress_positions(book([held]), None), the_market, [Shock("iv", 0, 2.0, 0, 1)])
    assert bs_price(100, 100, 1.0, 0.05, 0.2, OPTION_CALL) == pytest.approx(10.4506, abs=1e-4)
    assert result.trades[0].loss_from_marks == pytest.approx((9.0 - 10.4506) * LOT, abs=0.01)


def test_a_leg_expiring_today_is_worth_its_intrinsic_value():
    today = market(25100, {(25000, OPTION_CALL): 100.0}, DAY)
    assert StressEngine(MODEL).leg_value(next(iter(today.quotes)), 1, today, Shock("none", 0)) == pytest.approx(100.0)


def test_the_stress_never_includes_a_position_the_book_does_not_hold():
    fly = open_trade("fly-1", FLY, 200, short_fly(25000, 200), EXPIRY, cash_flow=8000.0)
    positions = stress_positions(book([fly]), None)
    assert [p.trade_id for p in positions] == ["fly-1"]


def test_expired_quotes_are_refused():
    old = market(25000, PRICES, date(2026, 10, 12))
    fly = open_trade("fly-1", FLY, 200, short_fly(25000, 200), date(2026, 10, 12), cash_flow=0.0)
    with pytest.raises(ValueError, match="expired"):
        StressEngine(MODEL).run(stress_positions(book([fly]), None), old, [Shock("x", 0)])


def test_the_forward_not_the_spot_is_what_moves_and_prices():
    """Same spot, a future 100 points higher: an at-the-money call is worth more, priced on the future."""
    expiry = DAY + timedelta(days=30)
    near, far = (market(25000, {(25000, OPTION_CALL): 300.0}, expiry, forward=f) for f in (25000, 25100))
    value = [StressEngine(MODEL).leg_value(next(iter(m.quotes)), 1, m, Shock("none", 0)) for m in (near, far)]
    assert value[1] - value[0] > 40


def test_a_leg_without_a_traded_future_fails_closed():
    expiry = DAY + timedelta(days=30)
    the_market = market(25000, {(25000, OPTION_CALL): 300.0}, expiry)
    no_future = type(the_market)(DAY, 25000, 0.065, the_market.quotes, {})
    with pytest.raises(ValueError, match="no usable NIFTY future"):
        StressEngine(MODEL).leg_value(next(iter(no_future.quotes)), 1, no_future, Shock("none", 0))


def test_the_proposals_pads_and_charges_count_in_the_stress_loss():
    """Judge 43 minor 1: with real charges and Rs 1 pads the proposal's loss from entry exceeds its loss from its mark,
    and a limit between the two refuses it: counting it from its mark would let it through."""
    condor = proposal("condor-1", CONDOR, 200, short_condor(25500, 24500, 200), EXPIRY)
    rule = StressLoss(StressEngine(MODEL), SimulatorTradeCosts(CHARGES), SCENARIOS, 1e9)
    the_market = market(25000, PRICES, EXPIRY)
    worst = max(rule.results(condor, book(), the_market), key=lambda r: r.counted_loss)
    from_mark, from_entry = worst.trades[0].loss_from_marks, worst.trades[0].loss_from_entry
    assert from_entry - from_mark > 4 * LOT  # at least the four Rs 1 pads, plus charges
    between = StressLoss(StressEngine(MODEL), SimulatorTradeCosts(CHARGES), SCENARIOS, (from_mark + from_entry) / 2)
    assert not between.check(condor, book(), the_market).ok
