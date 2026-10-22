"""Protocol sections 5-7 on a synthetic panel: entry only when every leg traded, the cap with the cycle's own lot, the
exits (trigger close, planned close, settlement; never another day), incomplete exits kept and flagged, pads and
charges, and the naked measurements."""

from datetime import timedelta

import pytest
from edge1study.structures import NS, NT, SC2, SC3, SF, structure
from edge1study.trade import BAD, CAP, EXP, SL2, T21, TAKEN, TP50, UNTRADED, run_trade

from fno.research_engine.cycle_costs import PositionCosts
from fno.research_engine.structures import NakedShortLeg, position_value

from .edge1_fakes import DAYS, ENTRY, EXIT, EXPIRY, cycle, flat_prices, panel, terms


def run(code, exit_rule, day_prices=None, settle=23000.0, lot=65, capped=True, pad=1.0):
    return run_trade(structure(code), panel(day_prices or {}), cycle(), terms(lot, pad), exit_rule, DAYS,
                     lambda expiry: settle, capped)  # fmt: skip


def test_a_flat_market_takes_the_widest_width_inside_the_cap_and_exits_at_the_planned_close():
    trade = run(SC2, T21)
    assert trade.status == TAKEN and trade.exit_day == EXIT and trade.exit_how == "planned"
    assert not trade.incomplete_exit
    assert trade.gross == pytest.approx(0.0) and trade.net == pytest.approx(-(trade.charges + trade.pads))
    assert trade.pads == pytest.approx(2 * 4 * 1.0 * 65)


def test_the_cap_uses_the_cycles_own_lot():
    """Credit 60: a 300 wing loses (300 - 60) x 65 = 15,600 > 10,000, so 200 is taken; 25 units fit 300; 200 fit
    none."""
    assert run(SC2, T21, lot=65).width == 200.0 and run(SC2, T21, lot=65).credit == pytest.approx(60.0)
    assert run(SC2, T21, lot=25).width == 300.0
    assert run(SC2, T21, lot=200).status == CAP


def test_an_untraded_leg_at_entry_means_no_trade():
    short_call = run(SC2, T21).legs[0].contract  # the same at every width: no width can be filled
    found = run(SC2, T21, {ENTRY: (23000.0, flat_prices(23000.0), {short_call})})
    assert found.status == UNTRADED
    wing = run(SC2, T21).legs[2].contract  # only the 200 width's wing: the next width is taken instead
    assert run(SC2, T21, {ENTRY: (23000.0, flat_prices(23000.0), {wing})}).width == 100.0


def test_an_untraded_leg_at_the_planned_exit_is_kept_and_flagged_incomplete():
    wing = run(SC2, T21).legs[2].contract
    trade = run(SC2, T21, {EXIT: (23000.0, flat_prices(23000.0), {wing})})
    assert trade.status == TAKEN and trade.incomplete_exit and trade.exit_day == EXIT


def test_sl2_exits_at_the_first_fully_traded_close_with_a_loss_of_twice_the_credit():
    base = run(SC2, SL2)
    crash = ENTRY + timedelta(days=5)
    untraded_day = ENTRY + timedelta(days=3)
    far_call = next(leg.contract for leg in base.legs if leg.side == 1 and leg.contract[1] == "CE")
    moves = {untraded_day: (21000.0, flat_prices(21000.0), {far_call}),  # fires, possible, but a leg is untraded
             crash: (21000.0, flat_prices(21000.0), set())}  # fmt: skip
    trade = run(SC2, SL2, moves)
    assert trade.exit_day == crash and trade.exit_how == "trigger"
    mark = -position_value(trade.legs, [flat_prices(21000.0)[leg.contract] for leg in trade.legs])
    assert mark >= 3 * trade.credit


def test_tp50_exits_when_half_the_credit_is_earned():
    calm = ENTRY + timedelta(days=4)
    decayed = {k: v * 0.3 for k, v in flat_prices(23000.0).items()}
    trade = run(SC2, TP50, {calm: (23000.0, decayed, set())})
    assert trade.exit_day == calm and trade.exit_how == "trigger" and trade.gross > 0


def marked(multiple: float) -> dict:
    """Entry-day prices with both shorts moved alike: the mark (cost to close) is `multiple` x credit and each
    vertical stays inside [0, width]."""
    base, prices = run(SC2, T21), dict(flat_prices(23000.0))
    for leg in base.legs:
        if leg.side == -1:
            prices[leg.contract] += (multiple - 1.0) * base.credit / 2
    return prices


@pytest.mark.parametrize(("rule", "multiple", "fires"), [(SL2, 2.5, False), (SL2, 3.0, True), (TP50, 0.45, True),
                                                         (TP50, 0.55, False)])  # fmt: skip
def test_the_triggers_fire_at_exactly_3x_and_half_the_credit(rule, multiple, fires):
    day = ENTRY + timedelta(days=4)
    trade = run(SC2, rule, {day: (23000.0, marked(multiple), set())})
    assert (trade.exit_day == day) is fires and (trade.exit_how == "trigger") is fires


def test_no_trigger_means_the_planned_close_never_another_day():
    trade = run(SC2, SL2)
    assert trade.exit_day == EXIT and trade.exit_how == "planned"


def test_exp_settles_at_intrinsic_with_settlement_charges_and_no_exit_pad():
    trade = run(SC2, EXP, settle=23000.0)
    assert trade.exit_day == EXPIRY and trade.exit_how == "settlement"
    assert trade.gross == pytest.approx(trade.credit * 65)  # every leg expires worthless at 23,000
    assert trade.pads == pytest.approx(4 * 1.0 * 65)
    assert trade.net == pytest.approx(trade.gross - trade.charges - trade.pads)
    breach = run(SC2, EXP, settle=24500.0)
    assert breach.gross < 0 and breach.charges > trade.charges  # settlement charges on in-the-money legs


def test_the_pad_level_moves_the_net_only_through_the_pads():
    one, two = run(SC2, T21, pad=1.0), run(SC2, T21, pad=2.0)
    assert two.pads == pytest.approx(2 * one.pads) and two.gross == pytest.approx(one.gross)


def test_sc3_sells_further_out_than_sc2():
    sc2, sc3 = run(SC2, T21).legs, run(SC3, T21).legs
    assert sc3[0].strike > sc2[0].strike and sc3[1].strike < sc2[1].strike


def test_sf_sells_the_atm_body():
    legs = run(SF, T21).legs
    assert legs[0].strike == legs[1].strike == 23000.0


def test_the_naked_measurements_have_no_wings_and_no_cap():
    strangle, straddle = run(NS, T21, capped=False), run(NT, T21, capped=False)
    assert len(strangle.legs) == 2 and {leg.side for leg in strangle.legs} == {-1}
    assert [leg.strike for leg in straddle.legs] == [23000.0, 23000.0]
    with pytest.raises(NakedShortLeg):
        PositionCosts(terms()).max_loss(list(strangle.legs), [100.0, 100.0])  # the engine still refuses naked legs


def test_impossible_entry_prices_are_skipped():
    flat = {k: 50.0 for k in flat_prices(23000.0)}  # shorts no dearer than wings: a credit of 0, not strictly inside
    assert run(SC2, T21, {ENTRY: (23000.0, flat, set())}).status == BAD


def impossible(prices: dict, base) -> dict:
    """The put wing priced above the short put: a put spread worth more than its width (stale closes)."""
    short_put = next(leg.contract for leg in base.legs if leg.side == -1 and leg.contract[1] == "PE")
    wing = next(leg.contract for leg in base.legs if leg.side == 1 and leg.contract[1] == "PE")
    return {**prices, short_put: prices[wing] + base.width + 50.0}


def test_a_planned_exit_at_an_impossible_mark_is_kept_and_flagged_out_of_the_decided_mean():
    base = run(SC2, T21)
    trade = run(SC2, T21, {EXIT: (23000.0, impossible(flat_prices(23000.0), base), set())})
    assert trade.status == TAKEN and trade.impossible_exit and trade.incomplete_exit
    assert not base.impossible_exit and not base.incomplete_exit


def test_a_trigger_never_fires_on_an_impossible_mark():
    base = run(SC2, SL2)
    day = ENTRY + timedelta(days=4)
    trade = run(SC2, SL2, {day: (23000.0, impossible(flat_prices(23000.0), base), set())})
    assert trade.exit_day == EXIT and trade.exit_how == "planned"  # it would fire at 3 x credit if it were believed


def test_a_possible_mark_with_an_untraded_leg_never_fires():
    """The short call untraded: its settlement proxy puts the mark inside the bounds and above 3 x credit."""
    base, day = run(SC2, SL2), ENTRY + timedelta(days=4)
    short_call = next(leg.contract for leg in base.legs if leg.side == -1 and leg.contract[1] == "CE")
    trade = run(SC2, SL2, {day: (23000.0, marked(3.6), {short_call})})
    assert trade.exit_day == EXIT and trade.exit_how == "planned"
