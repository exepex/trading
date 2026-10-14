"""Story C2 criteria 1, 2, 5 and 6: per-trade loss, open trades, exposure and margin room, each just inside and just
outside its limit."""

from datetime import timedelta

import pytest

from fno.constants import OPTION_CALL
from fno.research_engine.cycle_costs import CycleTerms, PositionCosts
from fno.research_engine.structures import BOUGHT, SOLD
from fno.risk.rules import ExposureLimit, MarginRoom, MaxLossPerTrade, MaxOpenTrades
from fno.risk.settings import ExposureSettings
from fno.risk.stress import StressEngine
from fno.risk.trade_costs import SimulatorTradeCosts

from .builders import CHARGES, CONDOR, DAY, FLY, LOT, MODEL, ZERO_CHARGES, book, market, open_trade, proposal, short_fly

EXPIRY = DAY + timedelta(days=20)
FLY_PRICES = {(25000, "CE"): 180.0, (25000, "PE"): 170.0, (25200, "CE"): 95.0, (24800, "PE"): 90.0}


class FixedCosts:
    """A trade-cost model with a given maximum loss, to test the rule's threshold exactly."""

    def __init__(self, max_loss: float, cash_flow: float = 0.0, funds: float = 0.0):
        self._max_loss, self._cash_flow, self._funds = max_loss, cash_flow, funds

    def max_loss(self, proposal, market):
        return self._max_loss

    def entry_cash_flow(self, proposal, market):
        return self._cash_flow

    def entry_funds(self, proposal, market):
        return self._funds


def _fly_proposal(lots: int = 1):
    return proposal("fly-new", FLY, 200, short_fly(25000, 200), EXPIRY, lots=lots)


@pytest.mark.parametrize(("loss", "ok"), [(9999.0, True), (10000.0, True), (10000.01, False), (10001.0, False)])
def test_max_loss_per_trade_threshold(loss, ok):
    verdict = MaxLossPerTrade(FixedCosts(loss), 10000).check(_fly_proposal(), book(), market(25000, {}, EXPIRY))
    assert verdict.ok is ok and verdict.numbers == {"max_loss_rs": loss, "limit_rs": 10000}
    assert ("above" in verdict.reason) is not ok


def test_max_loss_is_the_cycle_simulators_model_with_every_charge_and_pad():
    """Reuse of B2: the same legs and prices give the same rupees as `PositionCosts.max_loss` (2 lots, one order)."""
    the_proposal, the_market = _fly_proposal(lots=2), market(25000, FLY_PRICES, EXPIRY)
    legs = [p.leg for p in the_proposal.legs]
    expected = PositionCosts(CycleTerms(lot=2 * LOT, charges=CHARGES)).max_loss(
        legs, the_proposal.entry_prices(the_market)
    )
    assert SimulatorTradeCosts(CHARGES).max_loss(the_proposal, the_market) == pytest.approx(expected)
    # By hand: credit 180 + 170 - 95 - 90 = 165 on a 200 width: payoff loss 35 points x 130 units = 4,550, plus
    # pads (8 legs x Rs 1 x 130 = 1,040) plus entry and worst-case exit charges.
    assert expected > 4550 + 1040


def test_entry_cash_flow_counts_pads_and_charges():
    the_proposal, the_market = _fly_proposal(), market(25000, FLY_PRICES, EXPIRY)
    with_costs = SimulatorTradeCosts(CHARGES).entry_cash_flow(the_proposal, the_market)
    without = SimulatorTradeCosts(ZERO_CHARGES, pad=0.0).entry_cash_flow(the_proposal, the_market)
    assert without == pytest.approx(165 * LOT)
    legs, prices = [p.leg for p in the_proposal.legs], the_proposal.entry_prices(the_market)
    charges = PositionCosts(CycleTerms(lot=LOT, charges=CHARGES)).charges(legs, prices, True)
    assert with_costs == pytest.approx((165 - 4) * LOT - charges)  # 4 legs each Rs 1 worse


def test_entry_funds_are_the_bought_legs_at_their_fills_plus_charges_with_no_sold_credit():
    """Judge 77 addendum 3: the bought wings 95 + 90, each filled Rs 1 worse, plus every entry charge; the sold
    premium (180 + 170) is not counted."""
    the_proposal, the_market = _fly_proposal(), market(25000, FLY_PRICES, EXPIRY)
    legs, prices = [p.leg for p in the_proposal.legs], the_proposal.entry_prices(the_market)
    charges = PositionCosts(CycleTerms(lot=LOT, charges=CHARGES)).charges(legs, prices, True)
    assert SimulatorTradeCosts(CHARGES).entry_funds(the_proposal, the_market) == pytest.approx(
        (95 + 1 + 90 + 1) * LOT + charges
    )


@pytest.mark.parametrize(("open_now", "ok"), [(2, True), (3, False)])
def test_max_open_trades_allows_a_third_and_blocks_a_fourth(open_now, ok):
    trades = [open_trade(f"t{i}", FLY, 200, short_fly(25000, 200), EXPIRY, 0.0) for i in range(open_now)]
    verdict = MaxOpenTrades(3).check(_fly_proposal(), book(trades), market(25000, FLY_PRICES, EXPIRY))
    assert verdict.ok is ok and verdict.numbers["open_trades"] == open_now


# Exposure: options expiring today, so a 2% move is valued at intrinsic by hand. NIFTY 25,000; open: short call
# spread 25,000/25,200 (1 lot); proposed: short call spread 25,000/25,100. At +2% (25,500) the open spread loses
# (500 - 300) x 65 = Rs 13,000 and the proposal (500 - 400) x 65 = Rs 6,500: Rs 19,500 together.
SPREAD_PRICES = {(25000, "CE"): 0.0, (25200, "CE"): 0.0, (25100, "CE"): 0.0}


def _exposure_case():
    held = open_trade("open", CONDOR, 200, [(25000, OPTION_CALL, SOLD), (25200, OPTION_CALL, BOUGHT)], DAY, 0.0)
    new = proposal("new", CONDOR, 100, [(25000, OPTION_CALL, SOLD), (25100, OPTION_CALL, BOUGHT)], DAY)
    return new, book([held]), market(25000, SPREAD_PRICES, DAY)


def _exposure(max_move_loss: float, max_iv_loss: float = 15000) -> ExposureLimit:
    return ExposureLimit(StressEngine(MODEL), ExposureSettings(2, max_move_loss, 5, max_iv_loss))


def test_a_proposal_pushing_the_2pct_move_loss_above_the_setting_is_blocked():
    new, the_book, the_market = _exposure_case()
    alone = _exposure(15000).check(new, book(), the_market)
    together = _exposure(15000).check(new, the_book, the_market)
    assert alone.ok and alone.numbers["move_loss_rs"] == pytest.approx(6500)
    assert not together.ok and together.numbers["move_loss_rs"] == pytest.approx(19500)
    assert "2% move loss Rs 19,500.00 above Rs 15,000.00" in together.reason


@pytest.mark.parametrize(("limit", "ok"), [(19500.0, True), (19499.99, False)])
def test_exposure_move_limit_just_inside_and_just_outside(limit, ok):
    assert _exposure(limit).check(*_exposure_case()).ok is ok


def test_exposure_iv_rise_limit_just_inside_and_just_outside():
    """A short call 20 days out loses when IV rises 5 points; the limit at that loss passes, a paisa less refuses."""
    the_market = market(25000, {(25000, "CE"): 300.0}, EXPIRY, iv=0.12)
    short_call = proposal("call", CONDOR, 100, [(25000, OPTION_CALL, SOLD)], EXPIRY)
    loss = _exposure(1e9, 1e9).check(short_call, book(), the_market).numbers["iv_rise_loss_rs"]
    assert loss > 0
    assert _exposure(1e9, loss).check(short_call, book(), the_market).ok
    assert not _exposure(1e9, loss - 0.01).check(short_call, book(), the_market).ok


class FixedStressedMargin:
    method = "multiplier"

    def __init__(self, per_trade: float):
        self.per_trade = per_trade

    def margin(self, terms, day):
        return self.per_trade * terms.lots

    def margin_at_entry(self, terms, day):
        return self.per_trade * terms.lots

    def record(self):
        return {"method": self.method}


def test_margin_room_counts_every_open_trade_and_the_proposal_against_cash_after_entry():
    """Cash 100,000, marked equity 90,000 (a short structure's marked loss): the lower counts. The proposal receives
    Rs 1,000 net and is marked at -Rs 1,300 (pads and charges), so available after entry = min(101,000, 89,700)."""
    held = open_trade("open", FLY, 200, short_fly(25000, 200), EXPIRY, 0.0)
    the_book = book([held], cash=100_000.0, marked=90_000.0)
    held_marks = {(25000, "PE"): 10_000 / 65 - 20.0, (25200, "CE"): 0.0, (24800, "PE"): 0.0}  # held: -10,000
    the_market = market(25000, {(25000, "CE"): 20.0} | held_marks, EXPIRY)
    new = proposal("new", CONDOR, 100, [(25000, OPTION_CALL, SOLD)], EXPIRY)  # marked at 20 x -65 = -1,300
    costs = FixedCosts(0.0, cash_flow=1000.0)
    inside = MarginRoom(FixedStressedMargin(44_850.0), costs).check(new, the_book, the_market)
    outside = MarginRoom(FixedStressedMargin(44_850.01), costs).check(new, the_book, the_market)
    assert inside.numbers["available_after_entry_rs"] == pytest.approx(89_700.0)
    assert inside.ok and inside.numbers["needed_rs"] == pytest.approx(89_700.0)
    assert not outside.ok and inside.numbers["method"] == "multiplier"
