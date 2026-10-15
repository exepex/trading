"""Story C5 criteria 1-4 and 7: the bucket, open-risk and new-risk-per-day caps at, just under and just over the
owner's numbers, a position in two buckets (owner, 15 Oct 2026, "1 B"), trades opened and closed in the same session
("3 A"), the paper-account rule, and that a cap only refuses (never resizes a trade)."""

from dataclasses import replace
from datetime import timedelta

import pytest

from fno.config import load_app_config
from fno.constants import BUCKET_BEARISH, BUCKET_BULLISH, BUCKET_LONG_VOL, BUCKET_SHORT_VOL, RISK_PROFILE_BOOKS
from fno.risk.buckets import Bucket
from fno.risk.caps import BucketCap, NewRiskPerDay, OpenRiskCap, PaperAccountSize
from fno.risk.inputs import SessionTrade
from fno.risk.manager import RiskManager
from fno.risk.open_risk import PositionRisk
from fno.risk.profile_settings import profile_settings

from .builders import DAY, FLY, START, book, market, open_trade, proposal, short_fly

CAPS = profile_settings(load_app_config(), RISK_PROFILE_BOOKS)
EXPIRY = DAY + timedelta(days=14)
SHORT_VOL, LONG_VOL = Bucket("NIFTY", BUCKET_SHORT_VOL), Bucket("NIFTY", BUCKET_LONG_VOL)
BULLISH, BEARISH = Bucket("NIFTY", BUCKET_BULLISH), Bucket("NIFTY", BUCKET_BEARISH)
NEW = proposal("new", FLY, 200, short_fly(25000, 200), EXPIRY)
MARKET = market(25000, {}, EXPIRY)


class FixedRisks:
    """The positions' buckets and maximum losses given directly, so each cap is tested at its exact number."""

    def __init__(self, held=(), session=None, own=(SHORT_VOL,), own_loss=10_000.0):
        self.held = {p.trade_id: p for p in held}
        self.session = session or {}
        self.own = PositionRisk("new", tuple(own), own_loss)

    def of_open(self, trade, market):
        return self.held[trade.trade_id]

    def of_proposal(self, proposal, market):
        return self.own

    def of_session(self, trade, market):
        return self.session[trade.trade_id]

    def book(self, session_known=True):
        trades = tuple(open_trade(i, FLY, 200, short_fly(25000, 200), EXPIRY, 0.0) for i in self.held)
        session = tuple(SessionTrade(i, ()) for i in self.session) if session_known else None
        return replace(book(trades), session_trades=session)


def _held(loss: float, *buckets: Bucket, trade_id="held") -> PositionRisk:
    return PositionRisk(trade_id, buckets or (SHORT_VOL,), loss)


def _check(rule_class, risks: FixedRisks, limit: float, session_known=True):
    return rule_class(risks, limit).check(NEW, risks.book(session_known), MARKET)


def test_the_caps_are_the_owners_numbers_of_15_oct_2026():
    assert (CAPS.bucket_cap_rs, CAPS.open_risk_cap_rs, CAPS.new_risk_per_day_rs) == (30_000, 150_000, 50_000)


@pytest.mark.parametrize(("held", "ok"), [(19_999.99, True), (20_000.0, True), (20_000.01, False)])
def test_bucket_cap_at_just_under_and_just_over_rs_30000(held, ok):
    verdict = _check(BucketCap, FixedRisks([_held(held)]), CAPS.bucket_cap_rs)
    group = verdict.numbers["groups"]["bucket NIFTY/short_volatility"]
    assert verdict.ok is ok and verdict.rule == "bucket_cap" and group["total_rs"] == held + 10_000
    assert ("above" in verdict.reason) is not ok


def test_another_bucket_does_not_count_against_this_one():
    risks = FixedRisks([_held(25_000.0, LONG_VOL, trade_id="other"), _held(20_000.0)])
    verdict = _check(BucketCap, risks, CAPS.bucket_cap_rs)
    group = verdict.numbers["groups"]["bucket NIFTY/short_volatility"]
    assert verdict.ok and group["counted_max_loss_rs"] == {"held": 20_000.0, "new": 10_000.0}


@pytest.mark.parametrize(("held", "ok"), [(19_999.99, True), (20_000.0, True), (20_000.01, False)])
def test_a_two_bucket_proposal_must_fit_both_buckets_with_its_full_loss(held, ok):
    """A credit vertical (bullish and short volatility): each bucket gets its full Rs 10,000; the fuller one decides."""
    risks = FixedRisks([_held(5_000.0, trade_id="vol"), _held(held, BULLISH, trade_id="bull")],
                       own=(BULLISH, SHORT_VOL))  # fmt: skip
    verdict = _check(BucketCap, risks, CAPS.bucket_cap_rs)
    groups = verdict.numbers["groups"]
    assert groups["bucket NIFTY/bullish"]["total_rs"] == held + 10_000
    assert groups["bucket NIFTY/short_volatility"]["total_rs"] == 15_000.0
    assert verdict.ok is ok


@pytest.mark.parametrize(("held", "ok"), [(19_999.99, True), (20_000.0, True), (20_000.01, False)])
def test_a_held_two_bucket_position_counts_in_each_of_its_buckets(held, ok):
    """A held debit vertical (bearish and long volatility) counts its full loss against a long-volatility proposal."""
    risks = FixedRisks([_held(held, BEARISH, LONG_VOL, trade_id="put_debit")], own=(LONG_VOL,))
    assert _check(BucketCap, risks, CAPS.bucket_cap_rs).ok is ok
    assert _check(BucketCap, FixedRisks(risks.held.values(), own=(BULLISH,)), CAPS.bucket_cap_rs).ok  # not its bucket


@pytest.mark.parametrize(("held", "ok"), [(139_999.99, True), (140_000.0, True), (140_000.01, False)])
def test_open_risk_cap_at_just_under_and_just_over_rs_150000_counting_each_position_once(held, ok):
    two_sided = _held(held / 2, BULLISH, SHORT_VOL, trade_id="a")  # in two buckets, counted once here
    verdict = _check(
        OpenRiskCap, FixedRisks([two_sided, _held(held / 2, LONG_VOL, trade_id="b")]), CAPS.open_risk_cap_rs
    )
    assert verdict.ok is ok and verdict.rule == "open_risk_cap"
    assert verdict.numbers["groups"]["all open positions"]["total_rs"] == pytest.approx(held + 10_000, abs=1e-6)


@pytest.mark.parametrize(("today", "ok"), [(39_999.99, True), (40_000.0, True), (40_000.01, False)])
def test_new_risk_per_day_at_just_under_and_just_over_rs_50000(today, ok):
    """Only the session's trades count: an open trade from an earlier session is not in them."""
    risks = FixedRisks([_held(90_000.0, trade_id="earlier")], session={"today": today})
    verdict = _check(NewRiskPerDay, risks, CAPS.new_risk_per_day_rs)
    assert verdict.ok is ok and verdict.rule == "new_risk_per_day"
    assert set(verdict.numbers["groups"]["trades opened this session"]["counted_max_loss_rs"]) == {"today", "new"}


def test_a_trade_opened_and_closed_this_session_still_counts():
    """It is no longer open, so the open-risk cap does not see it; the session's new risk does (owner, "3 A")."""
    risks = FixedRisks([], session={"closed_today": 40_000.01})
    assert not _check(NewRiskPerDay, risks, CAPS.new_risk_per_day_rs).ok
    assert _check(OpenRiskCap, risks, CAPS.open_risk_cap_rs).ok


def test_a_book_whose_session_trades_are_unknown_fails_closed():
    risks = FixedRisks([], session={})
    manager = RiskManager([NewRiskPerDay(risks, CAPS.new_risk_per_day_rs)], {})
    decision = manager.evaluate(NEW, risks.book(session_known=False), MARKET)
    assert not decision.ok and "trades of this session are not known" in decision.reasons[0]


@pytest.mark.parametrize(("opened_with", "ok"), [(START, True), (500_000.0, False), (START + 0.01, False)])
def test_a_book_opened_with_any_other_cash_than_rs_20_lakh_trades_nothing(opened_with, ok):
    the_book = book()
    the_book = replace(the_book, state=replace(the_book.state, starting_cash=opened_with))
    verdict = PaperAccountSize(CAPS.paper_account_rs).check(NEW, the_book, MARKET)
    assert CAPS.paper_account_rs == START == 2_000_000.0 and verdict.ok is ok
    assert ok or "no trade until the owner decides" in verdict.reason


def test_a_cap_only_refuses_and_never_resizes_the_trade():
    """Over every cap at once, the decision is a refusal of the very proposal it was given, lots unchanged."""
    risks = FixedRisks([_held(200_000.0)], session={"held": 200_000.0})
    rules = [BucketCap(risks, 30_000), OpenRiskCap(risks, 150_000), NewRiskPerDay(risks, 50_000)]
    decision = RiskManager(rules, {}).evaluate(NEW, risks.book(), MARKET)
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
    assert verdict.ok and verdict.numbers["groups"]["bucket NIFTY/short_volatility"]["total_rs"] == total
    assert not BucketCap(risks, total - 0.01).check(NEW, book([held]), the_market).ok
