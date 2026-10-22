"""Criterion 1 (story MS-P1f): which fired decisions become tickets, and a ticket's laws are the trade's laws with
only the account limits relaxed."""

from dataclasses import replace

import pytest

from fno.school.constants import NoTradeReason, Outcome, RefusalReason, RoadCode, TicketReason
from fno.school.contracts.decisions import Decision, LegSpec
from fno.school.contracts.safety import LawResult
from fno.school.tickets.rules import ACCOUNT_LIMITS, after_laws, as_ticket, limit_trades, ticket_laws_pass
from tests.school.contracts import builders as b

PASS = LawResult("max_loss", True, None)


def fired(road: RoadCode, score: float) -> Decision:
    return Decision("CS1@1", road, b.SESSION, Outcome.TRADE, "", b.proposal_with(score=score))


def refused(reason: RefusalReason) -> LawResult:
    return LawResult(str(reason), False, reason)


def test_the_best_scores_stay_trades_and_the_rest_become_trade_limit_tickets():
    decisions = (fired(RoadCode.NIFTY_MONTHLY, 0.1), fired(RoadCode.BANKNIFTY_MONTHLY, 0.9),
                 fired(RoadCode.FINNIFTY_MONTHLY, 0.5))  # fmt: skip
    out = limit_trades(decisions, 2)
    assert [d.outcome for d in out] == [Outcome.TICKET, Outcome.TRADE, Outcome.TRADE]
    assert out[0].reason == TicketReason.TRADE_LIMIT and out[0].proposal == decisions[0].proposal


def test_at_the_limit_nothing_becomes_a_ticket_and_zero_allows_none():
    decisions = (fired(RoadCode.NIFTY_MONTHLY, 0.1), fired(RoadCode.BANKNIFTY_MONTHLY, 0.9))
    assert limit_trades(decisions, 2) == decisions
    assert {d.outcome for d in limit_trades(decisions, 0)} == {Outcome.TICKET}


def test_equal_scores_keep_the_fixed_road_order_and_non_trades_pass_through():
    quiet = Decision("CS1@1", RoadCode.NIFTY_WEEKLY, b.SESSION, Outcome.NO_TRADE, NoTradeReason.RULE_NOT_FIRED)
    decisions = (fired(RoadCode.MIDCPNIFTY_MONTHLY, 0.5), quiet, fired(RoadCode.NIFTY_MONTHLY, 0.5))
    out = limit_trades(decisions, 1)
    assert [d.outcome for d in out] == [Outcome.TICKET, Outcome.NO_TRADE, Outcome.TRADE]
    assert limit_trades((), 5) == ()


def test_a_trade_every_law_passed_stays_a_trade():
    decision = fired(RoadCode.NIFTY_MONTHLY, 0.5)
    assert after_laws(decision, (PASS,)) is decision and after_laws(decision, ()) is decision


@pytest.mark.parametrize("stop", [RefusalReason.DAILY_STOP, RefusalReason.BRAKE])
def test_a_stopped_driver_s_fired_rule_becomes_a_driver_stopped_ticket(stop):
    out = after_laws(fired(RoadCode.NIFTY_MONTHLY, 0.5), (PASS, refused(RefusalReason.OPEN_RISK), refused(stop)))
    assert (out.outcome, out.reason) == (Outcome.TICKET, TicketReason.DRIVER_STOPPED)


@pytest.mark.parametrize("results, reason", [
    ((refused(RefusalReason.BUCKET_CAP),), RefusalReason.BUCKET_CAP),  # an account cap without a stop
    ((refused(RefusalReason.DAILY_STOP), refused(RefusalReason.MISSING_QUOTE)), RefusalReason.DAILY_STOP),
    ((refused(RefusalReason.MAX_LOSS), refused(RefusalReason.BRAKE)), RefusalReason.MAX_LOSS)])  # fmt: skip
def test_any_other_refusal_stays_refused_with_the_first_reason(results, reason):
    out = after_laws(fired(RoadCode.NIFTY_MONTHLY, 0.5), results)
    assert (out.outcome, out.reason) == (Outcome.REFUSED, reason) and out.proposal is not None


def test_only_a_trade_goes_through_the_laws():
    with pytest.raises(ValueError):
        after_laws(as_ticket(fired(RoadCode.NIFTY_MONTHLY, 0.5), TicketReason.TRADE_LIMIT), ())


@pytest.mark.parametrize("reason", sorted(ACCOUNT_LIMITS))
def test_a_ticket_ignores_each_account_limit(reason):
    assert ticket_laws_pass((PASS, refused(reason)))


@pytest.mark.parametrize("reason", sorted(set(RefusalReason) - ACCOUNT_LIMITS))
def test_a_ticket_obeys_every_other_law(reason):
    assert not ticket_laws_pass((PASS, refused(reason)))


def test_the_account_limits_are_exactly_the_account_s_six():
    six = (RefusalReason.BUCKET_CAP, RefusalReason.OPEN_RISK, RefusalReason.NEW_RISK_DAY, RefusalReason.MARGIN_ROOM,
           RefusalReason.DAILY_STOP, RefusalReason.BRAKE)  # fmt: skip
    assert set(six) == ACCOUNT_LIMITS


def test_a_ticket_is_one_lot():
    decision = fired(RoadCode.NIFTY_MONTHLY, 0.5)
    two = replace(decision.proposal, legs=tuple(LegSpec(leg.key, leg.side, 2) for leg in decision.proposal.legs))
    with pytest.raises(ValueError):
        as_ticket(replace(decision, proposal=two), TicketReason.TRADE_LIMIT)
