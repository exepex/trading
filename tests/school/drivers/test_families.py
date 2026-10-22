"""Each family fires at its threshold and not just below it; history needs its full window (story MS-P1e, criteria
1 and 2). The thresholds are the numbers of story 3.2's table, read from the draft cards."""

from datetime import timedelta

import pytest

from fno.school.constants import NoTradeReason, Outcome, RoadCode
from fno.school.contracts.decisions import SpotPoint
from fno.school.drivers.expected_move import expected_move
from fno.school.drivers.history import SpotWindow
from fno.school.drivers.session_days import sessions_between
from tests.school.drivers import builders as b


def decide(code, road_day, snapshot, history, positions=()):
    return b.drivers()[code].decide(road_day, snapshot, history, positions)


def structure_of(decision):
    assert decision.outcome == Outcome.TRADE, (decision.outcome, decision.reason)
    return decision.proposal.structure


def not_fired(decision, reason=NoTradeReason.RULE_NOT_FIRED):
    return decision.outcome == Outcome.NO_TRADE and decision.reason == reason


class TestCappedSeller:
    def test_spot_above_the_window_mean_sells_a_put_spread_and_below_a_call_spread(self):
        road_day, snapshot = b.scene()
        above = decide("CS1", road_day, snapshot, b.history([b.SPOT - 0.01] * 20))
        below = decide("CS1", road_day, snapshot, b.history([b.SPOT + 0.01] * 20))
        assert structure_of(above) == "PCS" and structure_of(below) == "CCS"

    def test_spot_equal_to_the_mean_does_not_fire(self):
        road_day, snapshot = b.scene()
        assert not_fired(decide("CS1", road_day, snapshot, b.flat_history()))

    def test_the_short_strike_is_one_expected_move_from_spot(self):
        road_day, snapshot = b.scene()
        move = expected_move(snapshot, road_day.expiries[0]).straddle_mid
        proposal = decide("CS1", road_day, snapshot, b.history([b.SPOT - 1] * 20)).proposal
        short = next(leg for leg in proposal.legs if leg.side == "sell")
        assert abs(short.key.strike - (b.SPOT - move)) <= road_day.strike_step / 2

    @pytest.mark.parametrize("days, fires", [(19, False), (20, True), (45, True), (46, False)])
    def test_the_expiry_must_be_20_to_45_days_away(self, days, fires):
        road_day, snapshot = b.scene(days=(days,))
        decision = decide("CS1", road_day, snapshot, b.history([b.SPOT - 1] * 20))
        assert (decision.outcome == Outcome.TRADE) is fires
        assert fires or not_fired(decision, NoTradeReason.NO_EXPIRY_IN_WINDOW)


class TestDirectionalDebit:
    def test_a_new_window_high_buys_a_call_spread_and_a_low_a_put_spread(self):
        road_day, snapshot = b.scene()
        high = decide("DR1", road_day, snapshot, b.history([b.SPOT - 500] * 19 + [b.SPOT]))
        low = decide("DR1", road_day, snapshot, b.history([b.SPOT + 500] * 19 + [b.SPOT]))
        assert structure_of(high) == "CDS" and structure_of(low) == "PDS"

    def test_just_below_the_high_does_not_fire(self):
        road_day, snapshot = b.scene()
        assert not_fired(decide("DR1", road_day, snapshot, b.history([b.SPOT - 500] * 19 + [b.SPOT + 0.01])))

    def test_a_flat_window_has_no_direction(self):
        road_day, snapshot = b.scene()
        assert not_fired(decide("DR1", road_day, snapshot, b.flat_history()))

    def test_the_far_leg_is_one_strike_step_out(self):
        road_day, snapshot = b.scene()
        legs = decide("DR1", road_day, snapshot, b.history([b.SPOT - 500] * 19 + [b.SPOT])).proposal.legs
        assert sorted(leg.key.strike for leg in legs) == [b.SPOT, b.SPOT + road_day.strike_step]


class TestDebitBuyer:
    @staticmethod
    def history_at(scale: float, road_day, snapshot):
        """A zigzag window whose realised straddle-equivalent is `scale` times the implied straddle."""
        expiry = road_day.expiries[0]
        implied = expected_move(snapshot, expiry).straddle_mid
        sessions = sessions_between(b.CALENDAR, b.SESSION, expiry)
        trial = [b.SPOT * (1.01 if i % 2 else 0.99) for i in range(20)]
        realised = SpotWindow(tuple(trial)).straddle_equivalent(b.SPOT, sessions)
        # the zigzag's log returns scale linearly with its amplitude
        amplitude = 0.01 * scale * implied / realised
        return b.history([b.SPOT * (1 + amplitude if i % 2 else 1 - amplitude) for i in range(20)])

    def test_realised_above_implied_buys_an_iron_fly_and_just_below_does_not(self):
        road_day, snapshot = b.scene()
        above = decide("DB1", road_day, snapshot, self.history_at(1.0001, road_day, snapshot))
        below = decide("DB1", road_day, snapshot, self.history_at(0.9999, road_day, snapshot))
        assert structure_of(above) == "BF" and not_fired(below)

    def test_the_fly_is_long_at_the_money_and_inside_the_cap(self):
        road_day, snapshot = b.scene()
        proposal = decide("DB1", road_day, snapshot, self.history_at(2.0, road_day, snapshot)).proposal
        bought = {leg.key.strike for leg in proposal.legs if leg.side == "buy"}
        assert bought == {b.SPOT} and proposal.net_premium < 0 and proposal.max_loss <= b.CAP


class TestWeeklySeller:
    @pytest.mark.parametrize("days, fires", [(1, True), (3, True), (4, False)])
    def test_it_enters_one_to_three_sessions_before_the_weekly_expiry(self, days, fires):
        road_day, snapshot = b.scene(RoadCode.NIFTY_WEEKLY, 25_000.0, 50.0, 75, (days,), vol=0.4)
        assert sessions_between(b.CALENDAR, b.SESSION, b.SESSION + timedelta(days=days)) == days
        decision = decide("WS1", road_day, snapshot, ())
        assert (decision.outcome == Outcome.TRADE) is fires
        assert fires or not_fired(decision, NoTradeReason.NO_EXPIRY_IN_WINDOW)

    def test_on_the_expiry_day_itself_there_is_no_entry(self):
        road_day, snapshot = b.scene(RoadCode.NIFTY_WEEKLY, 25_000.0, 50.0, 75, (0, 7), vol=0.4)
        assert not_fired(decide("WS1", road_day, snapshot, ()), NoTradeReason.NO_EXPIRY_IN_WINDOW)

    def test_it_sells_an_iron_condor_with_shorts_one_expected_move_out(self):
        road_day, snapshot = b.scene(RoadCode.NIFTY_WEEKLY, 25_000.0, 50.0, 75, (3,), vol=0.4)
        move = expected_move(snapshot, road_day.expiries[0]).straddle_mid
        proposal = decide("WS1", road_day, snapshot, ()).proposal
        shorts = sorted(leg.key.strike for leg in proposal.legs if leg.side == "sell")
        assert proposal.structure == "SC"
        assert shorts[0] == pytest.approx(25_000 - move, abs=25) and shorts[1] == pytest.approx(25_000 + move, abs=25)


class TestWidthLadder:
    @pytest.mark.parametrize("days, fires", [(29, False), (30, True), (45, True), (46, False)])
    def test_the_expiry_must_be_30_to_45_days_away(self, days, fires):
        road_day, snapshot = b.scene(days=(days,))
        for code in ("PS2", "PS3", "PS4"):
            decision = decide(code, road_day, snapshot, ())
            assert (decision.outcome == Outcome.TRADE) is fires

    def test_the_three_versions_widen_their_wings_within_the_cap(self):
        road_day, snapshot = b.scene()
        widths = []
        for code in ("PS2", "PS3", "PS4"):
            proposal = decide(code, road_day, snapshot, ()).proposal
            call_strikes = sorted(leg.key.strike for leg in proposal.legs if str(leg.key.kind) == "CE")
            widths.append(call_strikes[1] - call_strikes[0])
            assert proposal.max_loss <= b.CAP
        assert widths[0] < widths[1] < widths[2]

    def test_a_version_with_an_open_position_on_the_road_enters_nothing_new(self):
        road_day, snapshot = b.scene()
        ps4 = b.drivers()["PS4"]
        held = b.position_from(ps4.decide(road_day, snapshot, (), ()), ps4)
        assert not_fired(ps4.decide(road_day, snapshot, (), (held,)), NoTradeReason.POSITION_OPEN)
        other = b.position_from(ps4.decide(road_day, snapshot, (), ()), b.drivers()["PS3"])
        assert ps4.decide(road_day, snapshot, (), (other,)).outcome == Outcome.TRADE  # another version's does not count


class TestReference:
    def test_it_sells_a_condor_every_session_on_the_nearest_eligible_expiry(self):
        road_day, snapshot = b.scene(days=(1, 30))
        decision = decide("REF", road_day, snapshot, ())
        assert all(
            leg.key.expiry == road_day.expiries[1] for leg in decision.proposal.legs
        )  # 1 day left: below min_dte

    def test_it_is_not_limited_to_one_open_position(self):
        road_day, snapshot = b.scene()
        ref = b.drivers()["REF"]
        held = tuple(
            b.position_from(ref.decide(road_day, snapshot, (), ()), ref, position_id=f"p{n}") for n in range(3)
        )
        assert ref.decide(road_day, snapshot, (), held).outcome == Outcome.TRADE


@pytest.mark.parametrize("code", ["CS1", "DB1", "DR1"])
def test_19_sessions_of_history_is_not_enough_and_20_is_(code):
    road_day, snapshot = b.scene()
    spots = [b.SPOT * (1.01 if i % 2 else 0.99) for i in range(20)]
    short = decide(code, road_day, snapshot, b.history(spots[-19:]))
    assert not_fired(short, NoTradeReason.NOT_ENOUGH_HISTORY)
    full = decide(code, road_day, snapshot, b.history(spots))
    assert full.reason != NoTradeReason.NOT_ENOUGH_HISTORY


def test_history_from_the_day_itself_or_later_is_never_used():
    road_day, snapshot = b.scene()
    spots = [b.SPOT * (1.01 if i % 2 else 0.99) for i in range(20)]
    past = b.history(spots[-19:])
    leaked = (*past, *b.history([b.SPOT * 2], b.SESSION + timedelta(days=3)))
    assert not_fired(decide("CS1", road_day, snapshot, leaked), NoTradeReason.NOT_ENOUGH_HISTORY)


def test_a_spot_recorded_for_the_day_itself_is_not_history():
    road_day, snapshot = b.scene()
    spots = [b.SPOT * (1.01 if i % 2 else 0.99) for i in range(20)]
    past = b.history(spots[-19:])
    with_today = (*past, SpotPoint(b.SESSION, b.SPOT))
    assert not_fired(decide("CS1", road_day, snapshot, with_today), NoTradeReason.NOT_ENOUGH_HISTORY)
