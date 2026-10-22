"""Tests with independent oracles (judge J's survivors, story MS-P1e): hand-worked numbers and the story's own table,
never the code under test."""

from dataclasses import replace
from datetime import date, timedelta

import pytest

from fno.research_engine.cycles import TradingDays
from fno.risk.trade_costs import SimulatorTradeCosts
from fno.school.constants import ExitReason, NoTradeReason, Outcome, RoadCode
from fno.school.drivers.card_params import CardParams
from fno.school.drivers.entry import EntryContext
from fno.school.drivers.exits import net_if_closed
from fno.school.drivers.expected_move import ExpectedMove
from fno.school.drivers.families_directional import DebitBuyer
from fno.school.drivers.proposals import Plan, ProposalBuilder
from fno.school.drivers.shapes import ExpectedMoveCondor
from fno.school.drivers.wiring import build_drivers
from tests.risk.builders import ZERO_CHARGES
from tests.school.contracts import builders as cb
from tests.school.drivers import builders as b
from tests.school.drivers.test_exits import repriced


def decide(code, road_day, snapshot, history=(), positions=(), drivers=None):
    return (drivers or b.drivers())[code].decide(road_day, snapshot, history, positions)


# --- the cap, the score ------------------------------------------------------------------------------------------


def test_a_proposal_whose_loss_equals_the_cap_exactly_is_allowed_and_one_paisa_less_is_not():
    road_day, snapshot = b.scene()
    plan = Plan(road_day.expiries[0], ExpectedMoveCondor(b.SPOT, 1720.0), (400.0, 300.0, 200.0, 100.0))
    loose = ProposalBuilder(SimulatorTradeCosts(ZERO_CHARGES), 1e9).build(plan, road_day, snapshot)
    exact = ProposalBuilder(SimulatorTradeCosts(ZERO_CHARGES), loose.max_loss).build(plan, road_day, snapshot)
    tighter = ProposalBuilder(SimulatorTradeCosts(ZERO_CHARGES), loose.max_loss - 0.01).build(plan, road_day, snapshot)
    assert exact == loose and tighter is not None and tighter.max_loss < loose.max_loss


def test_the_score_is_the_cards_expected_net_over_the_maximum_loss():
    road_day, snapshot = b.scene()
    plan = Plan(road_day.expiries[0], ExpectedMoveCondor(b.SPOT, 1720.0), (300.0,), expected_net_rs=500.0)
    proposal = b.BUILDER.build(plan, road_day, snapshot)
    assert proposal.score == pytest.approx(500.0 / proposal.max_loss)
    assert b.BUILDER.build(replace(plan, expected_net_rs=0.0), road_day, snapshot).score == 0.0


def test_a_ranked_card_with_an_estimate_scores_with_it():
    cards = b.cards()
    ps4 = cards["PS4"]
    estimated = replace(ps4, parameters={**ps4.parameters, "expected_net_rs": 500.0})
    driver = {d.card.code: d for d in build_drivers({"PS4": estimated}, b.BUILDER, b.CALENDAR)}["PS4"]
    road_day, snapshot = b.scene()
    proposal = driver.decide(road_day, snapshot, (), ()).proposal
    assert proposal.score == pytest.approx(500.0 / proposal.max_loss) and proposal.score > 0


# --- the exit value, by hand --------------------------------------------------------------------------------------


def test_the_net_if_closed_buys_back_the_short_at_the_ask_and_sells_the_long_at_the_bid():
    # fixture: short 1000 PE (bid 10, ask 11), long 900 PE (bid 4, ask 5), lot 30, entry net Rs 95
    position, snapshot = cb.position(), cb.snapshot()
    assert net_if_closed(position, snapshot) == pytest.approx(95.0 + (4.0 - 11.0) * 30)


# --- RC1 takes its twin's exit -----------------------------------------------------------------------------------


def opened_as(decision, driver, session=b.SESSION):
    return b.position_from(decision, driver, session)


def test_rc1_condor_exits_follow_ps4_on_monthly_roads_and_ws1_on_the_weekly_road():
    rc1, ps4, ws1 = b.drivers()["RC1"], b.drivers()["PS4"], b.drivers()["WS1"]
    road_day, snapshot = b.scene()
    monthly = opened_as(ps4.decide(road_day, snapshot, (), ()), rc1)
    weekly_day, weekly_snap = b.scene(RoadCode.NIFTY_WEEKLY, 25_000.0, 50.0, 75, (3,), vol=0.4)
    weekly = opened_as(ws1.decide(weekly_day, weekly_snap, (), ()), rc1)
    assert monthly.structure == weekly.structure == "SC"
    # a loss of several times the credit: WS1 stops at 1.5x, the ladder has no stop
    assert rc1.review_exit(weekly, repriced(weekly_snap, 8.0), ()) == ExitReason.LOSS_LIMIT
    assert rc1.review_exit(monthly, repriced(snapshot, 3.0), ()) is None
    # 21 days held: the ladder's time exit, not WS1's (which has none)
    assert rc1.review_exit(monthly, replace(snapshot, session=b.SESSION + timedelta(days=21)), ()) == (
        ExitReason.DAYS_HELD
    )
    assert rc1.review_exit(weekly, replace(weekly_snap, session=b.SESSION + timedelta(days=2)), ()) is None


def test_rc1_vertical_and_fly_exits_follow_cs1_dr1_and_db1():
    rc1, cs1, dr1 = b.drivers()["RC1"], b.drivers()["CS1"], b.drivers()["DR1"]
    road_day, snapshot = b.scene()
    credit = opened_as(cs1.decide(road_day, snapshot, b.history([b.SPOT - 1] * 20), ()), rc1)
    debit = opened_as(dr1.decide(road_day, snapshot, b.history([b.SPOT - 500] * 19 + [b.SPOT]), ()), rc1)
    ten_sessions = replace(snapshot, session=b.SESSION + timedelta(days=14))
    assert (credit.structure, debit.structure) == ("PCS", "CDS")
    assert rc1.review_exit(credit, ten_sessions, ()) == ExitReason.SESSIONS_HELD  # CS1: 10 sessions
    twenty_one_days = replace(snapshot, session=b.SESSION + timedelta(days=21))
    assert rc1.review_exit(credit, twenty_one_days, ()) == ExitReason.SESSIONS_HELD
    # DR1 alone has the spot-through-mean exit; CS1 does not
    tomorrow = b.SESSION + timedelta(days=1)
    _, below = b.scene(spot=b.SPOT - 1, session=tomorrow, days=(29, 59))
    flat = b.history([b.SPOT] * 20, tomorrow)
    assert rc1.review_exit(debit, below, flat) == ExitReason.SPOT_THROUGH_MEAN
    assert rc1.review_exit(credit, below, flat) is None


# --- calendar gaps at entry --------------------------------------------------------------------------------------


YEAR_END = TradingDays(b.WeekdayCalendar(date(2026, 12, 31)))


class Refuses(b.WeekdayCalendar):
    def session_kind(self, day):
        raise b.CalendarError("the calendar cannot answer")


def drivers_on(calendar):
    return {d.card.code: d for d in build_drivers(b.cards(), b.BUILDER, TradingDays(calendar))}


def test_ws1_does_not_enter_when_the_calendar_cannot_count_the_sessions_to_expiry():
    session = date(2026, 12, 30)
    road_day, snapshot = b.scene(RoadCode.NIFTY_WEEKLY, 25_000.0, 50.0, 75, (5,), session=session, vol=0.4)
    decision = decide("WS1", road_day, snapshot, drivers=drivers_on(b.WeekdayCalendar(date(2026, 12, 31))))
    assert (decision.outcome, decision.reason) == (Outcome.NO_TRADE, NoTradeReason.NO_EXPIRY_IN_WINDOW)


def test_db1_does_not_enter_when_the_calendar_cannot_count_the_sessions_to_expiry():
    session = date(2026, 12, 10)
    road_day, snapshot = b.scene(session=session, days=(26, 56))  # expiry 5 Jan 2027, past the calendar
    history = b.history([b.SPOT * (1.05 if i % 2 else 0.95) for i in range(20)], session)
    full = decide("DB1", road_day, snapshot, history)
    assert full.outcome == Outcome.TRADE  # the same day with a full calendar does enter
    gap = decide("DB1", road_day, snapshot, history, drivers=drivers_on(b.WeekdayCalendar(date(2026, 12, 31))))
    assert (gap.outcome, gap.reason) == (Outcome.NO_TRADE, NoTradeReason.NO_EXPIRY_IN_WINDOW)


def test_the_edge1_controls_do_not_enter_when_the_calendar_cannot_name_the_previous_session():
    road_day, snapshot = b.scene(days=(45, 75))
    assert decide("PS5", road_day, snapshot).outcome == Outcome.TRADE
    refused = decide("PS5", road_day, snapshot, drivers=drivers_on(Refuses()))
    assert (refused.outcome, refused.reason) == (Outcome.NO_TRADE, NoTradeReason.NO_EXPIRY_IN_WINDOW)


# --- one-position scope, RC1's minimum days, DB1 equality, ATM distance, ladder, bounds -------------------------


def test_another_roads_position_does_not_block_a_version_on_this_road():
    ps4 = b.drivers()["PS4"]
    road_day, snapshot = b.scene()
    elsewhere = replace(b.position_from(ps4.decide(road_day, snapshot, (), ()), ps4), road=RoadCode.NIFTY_MONTHLY)
    assert ps4.decide(road_day, snapshot, (), (elsewhere,)).outcome == Outcome.TRADE


def test_rc1_never_picks_an_expiry_with_under_two_days_left():
    for n in range(30):
        session = b.SESSION + timedelta(days=n)
        road_day, snapshot = b.scene(days=(1, 30), session=session)
        decision = decide("RC1", road_day, snapshot)
        assert {leg.key.expiry for leg in decision.proposal.legs} == {session + timedelta(days=30)}
    only_tomorrow, snap = b.scene(days=(1,))
    assert decide("RC1", only_tomorrow, snap).reason == NoTradeReason.NO_EXPIRY_IN_WINDOW
    two_days, snap2 = b.scene(days=(2,), vol=0.4)
    assert decide("RC1", two_days, snap2).reason != NoTradeReason.NO_EXPIRY_IN_WINDOW


class FixedWindow:
    def __init__(self, value):
        self.value = value

    def straddle_equivalent(self, spot, sessions):
        return self.value


def test_db1_does_not_fire_when_realised_equals_implied_exactly():
    road_day, snapshot = b.scene()
    expiry = road_day.expiries[0]
    family = DebitBuyer(CardParams(b.cards()["DB1"]))

    class Context(EntryContext):
        def window(self, length):
            return FixedWindow(900.0)

        def move(self, expiry):
            return ExpectedMove(b.SPOT, 900.0)

    ctx = Context(road_day, snapshot, (), b.CALENDAR)
    assert family.plan(ctx) == NoTradeReason.RULE_NOT_FIRED
    assert isinstance(family.plan(Context(road_day, snapshot, (), b.CALENDAR)), NoTradeReason)
    ctx.window = lambda length: FixedWindow(900.01)
    assert not isinstance(family.plan(ctx), NoTradeReason) and expiry


def test_the_atm_strike_may_sit_two_steps_from_spot_but_not_three():
    road_day, snapshot = b.scene()
    first = road_day.expiries[0]

    def without_near_strikes(distance):
        kept = {k: q for k, q in snapshot.quotes.items() if k.expiry != first or abs(k.strike - b.SPOT) >= distance}
        return replace(snapshot, quotes=kept)

    assert decide("PS4", road_day, without_near_strikes(200.0)).outcome == Outcome.TRADE
    assert decide("PS4", road_day, without_near_strikes(300.0)).reason == NoTradeReason.NO_VALID_QUOTES


def test_the_ladder_wings_are_one_three_and_the_widest_that_fits():
    road_day, snapshot = b.scene()
    wings = {}
    for code in ("PS2", "PS3", "PS4"):
        calls = sorted(
            leg.key.strike for leg in decide(code, road_day, snapshot).proposal.legs if str(leg.key.kind) == "CE"
        )
        wings[code] = calls[1] - calls[0]
    assert wings["PS2"] == 100.0 and wings["PS3"] == 300.0 and wings["PS4"] > 300.0


def test_a_long_fly_that_costs_more_than_its_maximum_payoff_at_the_touch_is_never_proposed():
    road_day, snapshot = b.scene(spread=0.01)  # wide quotes: the touch price of a fly can exceed its wing width
    history = b.history([b.SPOT * (1.05 if i % 2 else 0.95) for i in range(20)])
    decision = decide("DB1", road_day, snapshot, history)
    if decision.outcome == Outcome.TRADE:
        proposal = decision.proposal
        width = max(leg.key.strike for leg in proposal.legs) - b.SPOT
        assert -proposal.net_premium / proposal.lot < width  # the fly's most it can pay is the wing width
    else:
        assert decision.reason == NoTradeReason.NO_STRUCTURE_UNDER_CAP
