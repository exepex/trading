"""Story B2 criteria 1-4 and 6: hand-worked cycles (prices written here) through the cycle simulator."""

from __future__ import annotations

import pytest

from fno.constants import CycleStatus
from fno.research_engine.cycles import Cycle
from fno.research_engine.simulator import CycleSimulator
from fno.research_engine.structures import LongIronFly, ShortCondor, ShortIronFly
from tests.research_engine.cycle_fixtures import (
    CE,
    CYCLE,
    LOT,
    PE,
    TERMS,
    cycle_panel,
    hand_order_charges,
    quotes,
    strikes_listed,
)

FLY_STRIKES = [23700.0 + 50 * i for i in range(13)]  # 23700 to 24300
CONDOR_STRIKES = [23200.0 + 50 * i for i in range(33)]  # 23200 to 24800
PADS = 8 * 1.0 * LOT  # four legs, entry and exit, Rs 1 each per unit


def simulate(structure, spot, entry, exit_, entry_settle=None, exit_settle=None, cycle=CYCLE):
    panel = cycle_panel(spot, quotes(entry, entry_settle), quotes(exit_, exit_settle))
    return CycleSimulator(panel, TERMS).simulate(cycle, structure)


def assert_money(result, gross, charges, net, max_loss, rupees):
    """Equal to the hand calculation, and to the rupee figures written in the test."""
    for got, hand, written in zip(
        (result.gross, result.charges, result.pads, result.net, result.max_loss),
        (gross, charges, PADS, net, max_loss),
        rupees,
    ):
        assert got == pytest.approx(hand, abs=1e-6) and round(got) == written


def test_short_iron_fly_by_hand():
    """Sell 24000 CE 300 and PE 280, buy 24300 CE 150 and 23700 PE 140 (credit 290, width 300); exit at 200, 250, 80,
    120. Gross = (100 + 30 - 70 - 20) x 65 = 2,600. Worst case at expiry: index at 24300 (or 23700), loss
    (300 - 290) x 65 = 650; exit there buys the 24000 CE back at 301 and the 24000 PE at 1, sells the wings at a
    tick."""
    entry = {**strikes_listed(FLY_STRIKES), (24000, CE): 300, (24000, PE): 280, (24300, CE): 150, (23700, PE): 140}
    exit_ = {**strikes_listed(FLY_STRIKES), (24000, CE): 200, (24000, PE): 250, (24300, CE): 80, (23700, PE): 120}
    r = simulate(ShortIronFly(), 24010.0, entry, exit_)
    entry_charges = sum(
        hand_order_charges(p, sell) for p, sell in ((299, True), (279, True), (151, False), (141, False))
    )
    exit_charges = sum(hand_order_charges(p, sell) for p, sell in ((201, False), (251, False), (79, True), (119, True)))
    worst_exit = sum(hand_order_charges(p, sell) for p, sell in ((301, False), (1, False), (0, True), (0, True)))
    charges = entry_charges + exit_charges
    assert r.status == CycleStatus.TRADED and r.width == 300
    assert [(leg.leg.strike, leg.leg.kind, leg.leg.side) for leg in r.legs] == [
        (24000, CE, -1), (24000, PE, -1), (24300, CE, 1), (23700, PE, 1)
    ]  # fmt: skip
    max_loss = 10 * LOT + entry_charges + PADS + worst_exit
    assert_money(r, 2600, charges, 2600 - charges - PADS, max_loss, (2600, 307, 520, 1773, 1448))


def test_short_condor_by_hand():
    """Spot 24000: sell the call nearest 24480 (24500) at 120 and the put nearest 23520 (23500) at 110, buy 24800 CE at
    30 and 23200 PE at 25 (credit 175); exit at 60, 150, 10, 40. Gross = (60 - 40 - 20 + 15) x 65 = 975; worst case
    loss (300 - 175) x 65 = 8,125."""
    entry = {**strikes_listed(CONDOR_STRIKES), (24500, CE): 120, (23500, PE): 110, (24800, CE): 30, (23200, PE): 25}
    exit_ = {**strikes_listed(CONDOR_STRIKES), (24500, CE): 60, (23500, PE): 150, (24800, CE): 10, (23200, PE): 40}
    r = simulate(ShortCondor(), 24000.0, entry, exit_)
    entry_charges = sum(hand_order_charges(p, sell) for p, sell in ((119, True), (109, True), (31, False), (26, False)))
    exit_charges = sum(hand_order_charges(p, sell) for p, sell in ((61, False), (151, False), (9, True), (39, True)))
    worst_exit = sum(hand_order_charges(p, sell) for p, sell in ((301, False), (1, False), (0, True), (0, True)))
    charges = entry_charges + exit_charges
    assert r.status == CycleStatus.TRADED and r.width == 300
    max_loss = 125 * LOT + entry_charges + PADS + worst_exit
    assert_money(r, 975, charges, 975 - charges - PADS, max_loss, (975, 231, 520, 224, 8873))


def test_long_iron_fly_by_hand_on_the_only_listed_width():
    """Only 23900, 24000 and 24100 are listed, so widths 300-150 are unavailable and 100 is used. Buy 24000 CE 300 and
    PE 290, sell 24100 CE 250 and 23900 PE 245 (debit 95); exit at 380, 200, 310, 150: gross (80 - 90 - 60 + 95) x 65
    = 1,625. Worst case: index at 24000, every leg worthless, loss 95 x 65 = 6,175."""
    strikes = [23900.0, 24000.0, 24100.0]
    entry = {**strikes_listed(strikes), (24000, CE): 300, (24000, PE): 290, (24100, CE): 250, (23900, PE): 245}
    exit_ = {**strikes_listed(strikes), (24000, CE): 380, (24000, PE): 200, (24100, CE): 310, (23900, PE): 150}
    r = simulate(LongIronFly(), 23990.0, entry, exit_)
    entry_charges = sum(
        hand_order_charges(p, sell) for p, sell in ((301, False), (291, False), (249, True), (244, True))
    )
    exit_charges = sum(
        hand_order_charges(p, sell) for p, sell in ((379, True), (199, True), (311, False), (151, False))
    )
    worst_exit = sum(hand_order_charges(p, sell) for p, sell in ((0, True), (0, True), (1, False), (1, False)))
    charges = entry_charges + exit_charges
    assert r.status == CycleStatus.TRADED and r.width == 100
    assert [(t.width, t.outcome) for t in r.widths_tried[:4]] == [
        (w, CycleStatus.MISSING_STRIKES) for w in (300, 250, 200, 150)
    ]
    max_loss = 95 * LOT + entry_charges + PADS + worst_exit
    assert_money(r, 1625, charges, 1625 - charges - PADS, max_loss, (1625, 353, 520, 752, 6963))


def fly_prices():
    return {**strikes_listed(FLY_STRIKES), (24000, CE): 300, (24000, PE): 280, (24300, CE): 150, (23700, PE): 140}


def test_an_untraded_leg_uses_its_settlement_price_flagged():
    entry = fly_prices()
    del entry[(23700, PE)]
    r = simulate(ShortIronFly(), 24010.0, entry, fly_prices(), entry_settle={(23700, PE): 141.0})
    leg = next(leg for leg in r.legs if leg.leg.contract == (23700, PE))
    assert r.status == CycleStatus.TRADED
    assert leg.entry.price == 141.0 and leg.entry.on_settlement and not leg.exit.on_settlement
    assert r.needs_settlement and r.no_settlement_net == 0.0 and r.net != 0.0


@pytest.mark.parametrize("side", ["entry", "exit"])
def test_three_of_four_legs_on_settlement_is_unfillable(side):
    flagged = {(24000, CE): 300.0, (24000, PE): 280.0, (24300, CE): 150.0}
    traded = {k: v for k, v in fly_prices().items() if k not in flagged}
    prices = {"entry": (traded, fly_prices(), flagged, None), "exit": (fly_prices(), traded, None, flagged)}[side]
    r = simulate(ShortIronFly(), 24010.0, *prices[:2], entry_settle=prices[2], exit_settle=prices[3])
    assert r.status == CycleStatus.UNFILLABLE and r.net == 0.0


def test_a_zero_settlement_is_no_price():
    """Judge 20: NSE's expiry-day settlement was 0.00 up to 30 Jan 2020; a 0.00 settlement is missing, not a price."""
    entry = fly_prices()
    del entry[(24300, CE)]
    r = simulate(ShortIronFly(), 24010.0, entry, fly_prices(), entry_settle={(24300, CE): 0.0})
    assert r.widths_tried[0].outcome == CycleStatus.UNFILLABLE and r.status == CycleStatus.UNFILLABLE


def test_a_zero_close_on_a_traded_leg_is_unfillable_at_exit():
    r = simulate(ShortIronFly(), 24010.0, fly_prices(), {**fly_prices(), (24300, CE): 0.0})
    assert r.status == CycleStatus.UNFILLABLE and r.width == 300 and r.net == 0.0


def test_a_credit_equal_to_the_width_is_bad_prices():
    """Sell 24000 CE and PE for 300 each, buy the 300-point wings for 150 each: credit 300 = width, cannot lose."""
    prices = {(24000, CE): 300, (24000, PE): 300, (24300, CE): 150, (23700, PE): 150}
    r = simulate(ShortIronFly(), 24010.0, prices, prices)
    assert r.status == CycleStatus.BAD_PRICES


def test_a_long_debit_of_zero_is_bad_prices():
    prices = {(24000, CE): 200, (24000, PE): 200, (24300, CE): 200, (23700, PE): 200}
    assert simulate(LongIronFly(), 24010.0, prices, prices).status == CycleStatus.BAD_PRICES


def ladder(atm_call, atm_put):
    """Long iron fly prices: debit 290, 230, 170, 100 and 48 at widths 300, 250, 200, 150 and 100 when the ATM pair
    costs 300 + 280."""
    wings = {300: (150, 140), 250: (180, 170), 200: (210, 200), 150: (245, 235), 100: (270, 262)}
    prices = {(24000, CE): atm_call, (24000, PE): atm_put}
    for width, (call, put) in wings.items():
        prices |= {(24000 + width, CE): call, (24000 - width, PE): put}
    return prices


def test_only_the_150_point_width_fits_under_the_cap():
    r = simulate(LongIronFly(), 24010.0, ladder(300, 280), ladder(300, 280))
    outcomes = [(t.width, t.outcome) for t in r.widths_tried]
    assert outcomes == [
        (300, CycleStatus.NO_TRADE_CAP), (250, CycleStatus.NO_TRADE_CAP), (200, CycleStatus.NO_TRADE_CAP),
        (150, CycleStatus.TRADED),
    ]  # fmt: skip
    assert r.status == CycleStatus.TRADED and r.width == 150 and r.max_loss <= 10_000
    assert r.widths_tried[2].max_loss > 10_000


def test_no_width_fits_is_no_trade_cap():
    r = simulate(LongIronFly(), 24010.0, ladder(400, 380), ladder(400, 380))
    assert r.status == CycleStatus.NO_TRADE_CAP and r.width is None and r.net == 0.0
    assert all(t.outcome == CycleStatus.NO_TRADE_CAP for t in r.widths_tried)


def test_no_wing_listed_at_all_is_missing_strikes():
    prices = {(24000, CE): 300, (24000, PE): 280, (24050, CE): 250, (23950, PE): 240}
    r = simulate(ShortIronFly(), 24010.0, prices, prices)
    assert r.status == CycleStatus.MISSING_STRIKES and len(r.widths_tried) == 5


def test_an_entry_day_not_before_the_exit_day_is_no_entry_window():
    cycle = Cycle(CYCLE.expiry, CYCLE.decision_day, CYCLE.exit_day, CYCLE.exit_day)
    r = simulate(ShortIronFly(), 24010.0, fly_prices(), fly_prices(), cycle=cycle)
    assert r.status == CycleStatus.NO_ENTRY_WINDOW and r.legs == ()


def test_cycle_status_is_exactly_the_six_values_b3_consumes():
    assert {s.value for s in CycleStatus} == {
        "traded", "no_trade_cap", "missing_strikes", "no_entry_window", "unfillable", "bad_prices",
    }  # fmt: skip
    with pytest.raises(ValueError):
        CycleStatus("no_trade")
