"""Story C5 criteria 1-4 and 7: the bucket, open-risk and new-risk-per-day caps at, just under and just over the
owner's numbers, the paper-account rule, and that a cap only refuses (never resizes a trade)."""

from dataclasses import replace
from datetime import timedelta

import pytest

from fno.config import load_app_config
from fno.constants import BUCKET_LONG_VOL, BUCKET_SHORT_VOL
from fno.risk.buckets import Bucket
from fno.risk.cap_settings import cap_settings
from fno.risk.caps import BucketCap, NewRiskPerDay, OpenRiskCap, PaperAccountSize
from fno.risk.manager import RiskManager
from fno.risk.open_risk import PositionRisk

from .builders import DAY, FLY, START, book, market, open_trade, proposal, short_fly

CAPS = cap_settings(load_app_config())
EXPIRY = DAY + timedelta(days=14)
SHORT_VOL, LONG_VOL = Bucket("NIFTY", BUCKET_SHORT_VOL), Bucket("NIFTY", BUCKET_LONG_VOL)
OWN = PositionRisk("new", SHORT_VOL, 10_000.0, DAY, True)
NEW = proposal("new", FLY, 200, short_fly(25000, 200), EXPIRY)
MARKET = market(25000, {}, EXPIRY)


class FixedRisks:
    """The positions' buckets and maximum losses given directly, so each cap is tested at its exact number."""

    def __init__(self, *held: PositionRisk):
        self.held = held

    def all(self, proposal, book, market):
        return [*self.held, OWN]


def _held(loss: float, bucket: Bucket = SHORT_VOL, opened_on=DAY, trade_id="held") -> PositionRisk:
    return PositionRisk(trade_id, bucket, loss, opened_on)


def test_the_caps_are_the_owners_numbers_of_15_oct_2026():
    assert (CAPS.bucket_cap_rs, CAPS.open_risk_cap_rs, CAPS.new_risk_per_day_rs) == (30_000, 150_000, 50_000)


@pytest.mark.parametrize(("held", "ok"), [(19_999.99, True), (20_000.0, True), (20_000.01, False)])
def test_bucket_cap_at_just_under_and_just_over_rs_30000(held, ok):
    verdict = BucketCap(FixedRisks(_held(held)), CAPS.bucket_cap_rs).check(NEW, book(), MARKET)
    assert verdict.ok is ok and verdict.rule == "bucket_cap" and verdict.numbers["total_rs"] == held + 10_000
    assert "bucket NIFTY/short_volatility" in verdict.reason
    assert ("above" in verdict.reason) is not ok


def test_another_bucket_does_not_count_against_this_one():
    risks = FixedRisks(_held(25_000.0, LONG_VOL, trade_id="other"), _held(20_000.0))
    verdict = BucketCap(risks, CAPS.bucket_cap_rs).check(NEW, book(), MARKET)
    assert verdict.ok and verdict.numbers["counted_max_loss_rs"] == {"held": 20_000.0, "new": 10_000.0}


@pytest.mark.parametrize(("held", "ok"), [(139_999.99, True), (140_000.0, True), (140_000.01, False)])
def test_open_risk_cap_at_just_under_and_just_over_rs_150000_across_every_bucket(held, ok):
    risks = FixedRisks(_held(held / 2, LONG_VOL, trade_id="a"), _held(held / 2, trade_id="b"))
    verdict = OpenRiskCap(risks, CAPS.open_risk_cap_rs).check(NEW, book(), MARKET)
    assert verdict.ok is ok and verdict.rule == "open_risk_cap"
    assert verdict.numbers["total_rs"] == pytest.approx(held + 10_000, abs=1e-6)


@pytest.mark.parametrize(("held", "ok"), [(39_999.99, True), (40_000.0, True), (40_000.01, False)])
def test_new_risk_per_day_at_just_under_and_just_over_rs_50000(held, ok):
    risks = FixedRisks(_held(held), _held(90_000.0, opened_on=DAY - timedelta(days=1), trade_id="yesterday"))
    verdict = NewRiskPerDay(risks, CAPS.new_risk_per_day_rs).check(NEW, book(), MARKET)
    assert verdict.ok is ok and verdict.rule == "new_risk_per_day"
    assert "yesterday" not in verdict.numbers["counted_max_loss_rs"]  # opened on another session: not new today


def test_an_open_trade_with_no_known_first_fill_day_fails_closed():
    manager = RiskManager([NewRiskPerDay(FixedRisks(_held(1.0, opened_on=None)), CAPS.new_risk_per_day_rs)], {})
    decision = manager.evaluate(NEW, book(), MARKET)
    assert not decision.ok and "no recorded first-fill day" in decision.reasons[0]


@pytest.mark.parametrize(("opened_with", "ok"), [(START, True), (500_000.0, False), (START + 0.01, False)])
def test_a_book_opened_with_any_other_cash_than_rs_20_lakh_trades_nothing(opened_with, ok):
    the_book = book()
    the_book = replace(the_book, state=replace(the_book.state, starting_cash=opened_with))
    verdict = PaperAccountSize(CAPS.paper_account_rs).check(NEW, the_book, MARKET)
    assert CAPS.paper_account_rs == START == 2_000_000.0 and verdict.ok is ok
    assert ok or "no trade until the owner decides" in verdict.reason


def test_a_cap_only_refuses_and_never_resizes_the_trade():
    """Over every cap at once, the decision is a refusal of the very proposal it was given, lots unchanged."""
    risks = FixedRisks(_held(200_000.0))
    rules = [BucketCap(risks, 30_000), OpenRiskCap(risks, 150_000), NewRiskPerDay(risks, 50_000)]
    decision = RiskManager(rules, {}).evaluate(NEW, book(), MARKET)
    assert not decision.ok and decision.proposal is NEW and decision.proposal.terms.lots == 1
    assert [r.split(":")[0] for r in decision.reasons] == ["bucket_cap", "open_risk_cap", "new_risk_per_day"]


def test_the_real_position_risks_count_the_held_trades_of_the_book():
    """Wired as the app wires them: a held fly in the same bucket adds its own B2 maximum loss to the proposal's."""
    from fno.risk.wiring import build_position_risks

    prices = {(25000, "CE"): 150.0, (25000, "PE"): 140.0, (25200, "CE"): 70.0, (24800, "PE"): 60.0}
    the_market = market(25000, prices, EXPIRY)
    risks = build_position_risks(load_app_config(), CAPS)
    held = open_trade("held", FLY, 200, short_fly(25000, 200), EXPIRY, cash_flow=10_000.0)
    total = risks.of_proposal(NEW, the_market).max_loss_rs + risks.of_open(held, the_market).max_loss_rs
    verdict = BucketCap(risks, total).check(NEW, book([held]), the_market)
    assert (
        verdict.ok
        and verdict.numbers["total_rs"] == total
        and set(verdict.numbers["counted_max_loss_rs"])
        == {
            "held",
            "new",
        }
    )
    assert not BucketCap(risks, total - 0.01).check(NEW, book([held]), the_market).ok
