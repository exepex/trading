"""The sized proposal (story MS-P1e): widest wings whose maximum loss, priced at the touch the fill will use, is
within the cap; credits and debits as filled; costs inside the maximum loss; and the no-trade reasons for what cannot
be built."""

from dataclasses import replace

import pytest

from fno.constants import SIDE_BUY
from fno.research_engine.cycle_costs import CycleTerms, PositionCosts
from fno.research_engine.structures import BOUGHT, SOLD, Leg
from fno.risk.trade_costs import SimulatorTradeCosts
from fno.school.constants import NoTradeReason, Outcome
from fno.school.drivers.proposals import ProposalBuilder
from tests.risk.builders import ZERO_CHARGES
from tests.school.drivers import builders as b


def independent_touch_loss(proposal, snapshot):
    """B2's cost model applied straight to the legs at the touch, not through the builder under test."""
    legs = [Leg(l.key.strike, str(l.key.kind), BOUGHT if l.side == SIDE_BUY else SOLD) for l in proposal.legs]  # noqa: E741
    prices = [snapshot.quote(l.key).ask if l.side == SIDE_BUY else snapshot.quote(l.key).bid for l in proposal.legs]
    return PositionCosts(CycleTerms(lot=proposal.lot, charges=ZERO_CHARGES)).max_loss(legs, prices)


def decide(code, road_day, snapshot, history=()):
    return b.drivers()[code].decide(road_day, snapshot, history, ())


def test_every_proposal_is_inside_the_cap_and_its_costs_inside_its_maximum_loss():
    road_day, snapshot = b.scene()
    for code in ("PS2", "PS3", "PS4", "REF", "RC1"):
        proposal = decide(code, road_day, snapshot).proposal
        assert 0 < proposal.max_loss <= b.CAP and 0 <= proposal.costs <= proposal.max_loss, code
        assert proposal.lot == road_day.lot.units and all(leg.lots == 1 for leg in proposal.legs)


def test_the_maximum_loss_is_the_cost_model_at_the_touch():
    road_day, snapshot = b.scene()
    proposal = decide("PS4", road_day, snapshot).proposal
    assert proposal.max_loss == pytest.approx(independent_touch_loss(proposal, snapshot))
    assert proposal.costs == pytest.approx(240.0)  # four legs x 2 sides x Rs 1 pad x 30 units; zero charges here


def test_the_net_premium_is_what_the_touch_pays_a_credit_positive_and_a_debit_negative():
    road_day, snapshot = b.scene()
    credit = decide("PS4", road_day, snapshot).proposal
    expected = sum(
        (snapshot.quote(leg.key).bid if leg.side == "sell" else -snapshot.quote(leg.key).ask) for leg in credit.legs
    )
    assert credit.net_premium == pytest.approx(expected * 30) and credit.net_premium > 0
    debit = decide("DR1", road_day, snapshot, b.history([b.SPOT - 500] * 19 + [b.SPOT])).proposal
    assert debit.net_premium < 0


def test_wide_spreads_force_narrower_wings_so_a_fill_cannot_breach_the_cap():
    road_day, tight = b.scene(spread=0.002)
    _, wide = b.scene(spread=0.02)
    tight_proposal, wide_proposal = decide("PS4", road_day, tight).proposal, decide("PS4", road_day, wide).proposal

    def wing(proposal):
        calls = sorted(leg.key.strike for leg in proposal.legs if str(leg.key.kind) == "CE")
        return calls[1] - calls[0]

    assert wing(wide_proposal) < wing(tight_proposal)
    for proposal, snapshot in ((tight_proposal, tight), (wide_proposal, wide)):
        assert independent_touch_loss(proposal, snapshot) <= b.CAP
    assert wide_proposal.max_loss <= b.CAP


def test_a_cap_too_small_for_any_width_is_no_structure_under_cap():
    road_day, snapshot = b.scene()
    driver = b.drivers()["PS4"]
    driver.builder = ProposalBuilder(SimulatorTradeCosts(ZERO_CHARGES), 100.0)
    decision = driver.decide(road_day, snapshot, (), ())
    assert (decision.outcome, decision.reason) == (Outcome.NO_TRADE, NoTradeReason.NO_STRUCTURE_UNDER_CAP)


def test_a_missing_atm_quote_moves_the_straddle_to_the_next_strike_with_both_sides():
    road_day, snapshot = b.scene()
    first = road_day.expiries[0]
    stripped = replace(
        snapshot, quotes={k: q for k, q in snapshot.quotes.items() if k.expiry != first or k.strike != b.SPOT}
    )
    assert b.move(stripped, first).atm_strike == b.SPOT - 100  # the lower of two equally near strikes
    assert b.move(snapshot, first).atm_strike == b.SPOT
    decision = decide("PS4", road_day, stripped)
    assert decision.outcome == Outcome.TRADE and all(leg.key.strike != b.SPOT for leg in decision.proposal.legs)


def test_no_two_sided_straddle_at_all_is_no_valid_quotes_never_a_guess():
    road_day, snapshot = b.scene()
    first = road_day.expiries[0]
    puts_only = replace(
        snapshot, quotes={k: q for k, q in snapshot.quotes.items() if k.expiry != first or str(k.kind) == "PE"}
    )
    assert b.move(puts_only, first) is None
    decision = decide("PS4", road_day, puts_only)
    assert (decision.outcome, decision.reason) == (Outcome.NO_TRADE, NoTradeReason.NO_VALID_QUOTES)


def test_an_invalid_quote_is_never_priced_the_leg_moves_to_a_valid_strike():
    road_day, snapshot = b.scene()
    plain = decide("PS4", road_day, snapshot).proposal
    spoiled_strikes = {leg.key.strike for leg in plain.legs}
    spoiled = {k: replace(q, valid=False) if k.strike in spoiled_strikes else q for k, q in snapshot.quotes.items()}
    proposal = decide("PS4", road_day, replace(snapshot, quotes=spoiled)).proposal
    assert proposal is not None and not spoiled_strikes & {leg.key.strike for leg in proposal.legs}
