"""N0, RC1 and the EDGE1 controls (story MS-P1e, criteria 3-5)."""

import hashlib
from datetime import timedelta

import pytest

from fno.school.constants import ClosureReason, ExitReason, NoTradeReason, Outcome, RoadCode
from fno.school.contracts.roads import RoadStatus
from fno.school.drivers.card_params import CardParams
from fno.school.drivers.controls import draw_seed
from fno.school.drivers.exits import ExitPlan
from fno.school.drivers.scope import OutOfScope
from tests.school.contracts.builders import road_day as closed_road_day
from tests.school.drivers import builders as b

ROAD_SCENES = {
    RoadCode.NIFTY_MONTHLY: (25_000.0, 50.0, 75, (30, 60)),
    RoadCode.BANKNIFTY_MONTHLY: (50_000.0, 100.0, 30, (30, 60)),
    RoadCode.FINNIFTY_MONTHLY: (24_000.0, 50.0, 65, (30, 60)),
    RoadCode.MIDCPNIFTY_MONTHLY: (13_000.0, 25.0, 120, (30, 60)),
    RoadCode.NIFTY_WEEKLY: (25_000.0, 50.0, 75, (3, 10)),
}


def test_n0_gives_no_trade_n0_on_every_road_and_day():
    n0 = b.drivers()["N0"]
    for code, (spot, step, lot, days) in ROAD_SCENES.items():
        for offset in range(5):
            road_day, snapshot = b.scene(code, spot, step, lot, days, session=b.SESSION + timedelta(days=offset))
            decision = n0.decide(road_day, snapshot, b.history([spot] * 25, road_day.session), ())
            assert (decision.outcome, decision.reason, decision.proposal) == (Outcome.NO_TRADE, NoTradeReason.N0, None)
            assert decision.road == code


def test_n0_never_closes_a_position():
    n0, ps4 = b.drivers()["N0"], b.drivers()["PS4"]
    road_day, snapshot = b.scene()
    held = b.position_from(ps4.decide(road_day, snapshot, (), ()), ps4)
    assert n0.review_exit(held, snapshot, ()) is None


class TestRandomControl:
    def decisions(self, session, code=RoadCode.BANKNIFTY_MONTHLY):
        spot, step, lot, days = ROAD_SCENES[code]
        road_day, snapshot = b.scene(code, spot, step, lot, days, session=session)
        return b.drivers()["RC1"].decide(road_day, snapshot, (), ())

    def test_the_same_seed_gives_the_same_draw(self):
        first, again = self.decisions(b.SESSION), self.decisions(b.SESSION)
        assert first == again and first.outcome == Outcome.TRADE

    def test_another_seed_gives_another_draw(self):
        sessions = [b.SESSION + timedelta(days=n) for n in range(10)]
        draws = {self.decisions(s).proposal.legs for s in sessions}
        assert len(draws) > 3
        roads = {self.decisions(b.SESSION, code).proposal.structure for code in ROAD_SCENES}
        assert len(roads) >= 1

    def test_the_seed_is_the_sha256_of_session_driver_and_road(self):
        expected = int.from_bytes(hashlib.sha256(b"2026-11-02|RC1@1|BANKNIFTY-M").digest(), "big")
        assert draw_seed(b.SESSION, "RC1@1", "BANKNIFTY-M") == expected
        assert draw_seed(b.SESSION, "RC1@1", "NIFTY-M") != expected != draw_seed(b.SESSION, "REF@1", "BANKNIFTY-M")

    def test_every_draw_keeps_the_same_caps_and_stays_protected(self):
        shapes = set()
        for n in range(60):
            decision = self.decisions(b.SESSION + timedelta(days=n))
            assert decision.outcome == Outcome.TRADE
            proposal = decision.proposal
            assert 0 < proposal.max_loss <= b.CAP and proposal.lot == 30
            assert sum(leg.side == "sell" for leg in proposal.legs) <= sum(leg.side == "buy" for leg in proposal.legs)
            shapes.add(proposal.structure)
        assert shapes == {"PCS", "CCS", "CDS", "PDS", "BF", "SC"}

    def test_its_short_strike_stays_within_ten_steps_of_the_money(self):
        for n in range(40):
            proposal = self.decisions(b.SESSION + timedelta(days=n)).proposal
            near = [leg.key.strike for leg in proposal.legs if proposal.structure != "SC" or leg.side == "sell"][:2]
            assert all(abs(strike - b.SPOT) <= 10 * 100 + 1e-9 for strike in near[:1]), near

    def test_it_takes_the_exit_of_its_twin_family(self):
        rc1, cs1 = b.drivers()["RC1"], b.drivers()["CS1"]
        road_day, snapshot = b.scene()
        decision = next(d for d in (self.decisions(b.SESSION + timedelta(days=n)) for n in range(40))
                        if d.proposal.structure == "PCS")  # fmt: skip
        held = b.position_from(decision, rc1)
        later = b.SESSION + timedelta(days=14)
        later_day, later_snapshot = b.scene(session=later)
        assert rc1.review_exit(held, later_snapshot, ()) == cs1.review_exit(held, later_snapshot, ())
        assert rc1.review_exit(held, later_snapshot, ()) == ExitReason.SESSIONS_HELD  # 10 sessions in 14 days


def test_ps5_and_kl1_keep_edge1s_frozen_parameters():
    import edge1study.trade as trade
    from edge1study.runner import WIDTHS_BY_INDEX
    from edge1study.structures import structure as edge1_structure

    from fno.research_engine.cycles import EXIT_MIN_DAYS
    from fno.research_engine.structures import ShortCondor, ShortIronFly

    cards = b.cards()
    ps5, kl1 = CardParams(cards["PS5"]), CardParams(cards["KL1"])
    # PS5: BANKNIFTY SF TP50 (take profit at half the credit, closed on EDGE1's T21 day)
    assert ps5.number("exit_profit_share") == trade.TARGET_SHARE
    assert ps5.whole("exit_last_session_dte") == EXIT_MIN_DAYS
    assert tuple(float(w) for w in ps5.text("widths").split(",")) == WIDTHS_BY_INDEX["BANKNIFTY"]
    assert isinstance(edge1_structure("SF"), ShortIronFly)
    assert ps5.text("shape") == "fly"
    # KL1: NIFTY SC3 EXP (shorts at spot x 1.03 and x 0.97, held to expiry)
    assert kl1.number("short_offset") == edge1_structure("SC3").offset == 0.03
    assert tuple(float(w) for w in kl1.text("widths").split(",")) == WIDTHS_BY_INDEX["NIFTY"]
    assert isinstance(edge1_structure("SC3"), ShortCondor) and kl1.text("shape") == "condor"
    assert ExitPlan.from_params(kl1) == ExitPlan()  # no exit but expiry
    for control in (ps5, kl1):
        assert (control.whole("dte_min"), control.whole("dte_max")) == (30, 45)  # EDGE1's entry window
    assert cards["PS5"].roads == (RoadCode.BANKNIFTY_MONTHLY,) and cards["KL1"].roads == (RoadCode.NIFTY_MONTHLY,)


def test_ps5_enters_on_the_first_session_the_expiry_is_45_days_out_and_only_then():
    ps5 = b.drivers()["PS5"]
    first, snap_first = b.scene(days=(45, 75))  # Monday; the Friday before it had 48 days: first in window
    assert ps5.decide(first, snap_first, (), ()).outcome == Outcome.TRADE
    tuesday = b.SESSION + timedelta(days=1)  # Monday's expiry was 45 days away: already inside the window
    later, snap_later = b.scene(days=(44, 74), session=tuesday)
    assert ps5.decide(later, snap_later, (), ()).reason == NoTradeReason.NO_EXPIRY_IN_WINDOW


def test_kl1_shorts_sit_at_three_percent_from_spot():
    kl1 = b.drivers()["KL1"]
    road_day, snapshot = b.scene(RoadCode.NIFTY_MONTHLY, 25_000.0, 50.0, 75, (45, 75))
    proposal = kl1.decide(road_day, snapshot, (), ()).proposal
    shorts = sorted(leg.key.strike for leg in proposal.legs if leg.side == "sell")
    assert shorts == [24_250.0, 25_750.0] and proposal.structure == "SC"


def test_measurement_only_cards_carry_no_ranking_estimate():
    for code in ("PS5", "KL1"):
        assert not CardParams(b.cards()[code]).has("expected_net_rs")


def test_a_driver_is_not_called_on_a_closed_road_or_a_road_it_does_not_drive():
    ps5, n0 = b.drivers()["PS5"], b.drivers()["N0"]
    road_day, snapshot = b.scene(RoadCode.NIFTY_MONTHLY, 25_000.0, 50.0, 75, (45,))
    with pytest.raises(OutOfScope, match="does not drive"):
        ps5.decide(road_day, snapshot, (), ())
    with pytest.raises(OutOfScope, match="closed"):
        n0.decide(closed_road_day(status=RoadStatus(ClosureReason.HASH_MISMATCH)), snapshot, (), ())
    with pytest.raises(OutOfScope, match="snapshot"):
        n0.decide(road_day, b.scene()[1], (), ())
