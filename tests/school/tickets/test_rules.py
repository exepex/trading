"""Criterion 1 (story MS-P1f): which fired decisions trade, become tickets or are refused, with the same laws as
trades and only the account limits relaxed; later trades of a slot see the earlier ones."""

from dataclasses import replace

import pytest

from fno.school.constants import Outcome, RefusalReason, RoadCode, TicketReason
from fno.school.contracts.decisions import Decision, LegSpec
from fno.school.contracts.safety import LawResult
from fno.school.tickets.rules import ACCOUNT_LIMITS, as_ticket, classify, first_binding_refusal, ticket_laws_pass
from tests.school.contracts import builders as b

PASS = LawResult("max_loss", True, None)


def fired(road: RoadCode, score: float, max_loss: float = 2_500.0) -> Decision:
    return Decision("CS1@1", road, b.SESSION, Outcome.TRADE, "", b.proposal_with(score=score, max_loss=max_loss))


def refused(reason: RefusalReason) -> LawResult:
    return LawResult(str(reason), False, reason)


def always(*results):
    return lambda decision, accepted: results or (PASS,)


def outcomes(classified):
    return [(d.road, d.outcome, d.reason) for d, _ in classified]


def test_the_best_scores_trade_and_later_passing_rules_become_trade_limit_tickets():
    decisions = (fired(RoadCode.NIFTY_MONTHLY, 0.1), fired(RoadCode.BANKNIFTY_MONTHLY, 0.9),
                 fired(RoadCode.FINNIFTY_MONTHLY, 0.5))  # fmt: skip
    assert outcomes(classify(decisions, always(), 2)) == [
        (RoadCode.BANKNIFTY_MONTHLY, Outcome.TRADE, ""), (RoadCode.FINNIFTY_MONTHLY, Outcome.TRADE, ""),
        (RoadCode.NIFTY_MONTHLY, Outcome.TICKET, TicketReason.TRADE_LIMIT)]  # fmt: skip


def test_at_the_limit_nothing_is_a_ticket_zero_allows_no_trade_and_none_fired_gives_none():
    decisions = (fired(RoadCode.NIFTY_MONTHLY, 0.1), fired(RoadCode.BANKNIFTY_MONTHLY, 0.9))
    assert {o for _, o, _ in outcomes(classify(decisions, always(), 2))} == {Outcome.TRADE}
    assert {o for _, o, _ in outcomes(classify(decisions, always(), 0))} == {Outcome.TICKET}
    assert classify((), always(), 5) == ()


def test_equal_scores_keep_the_fixed_road_order():
    decisions = (fired(RoadCode.MIDCPNIFTY_MONTHLY, 0.5), fired(RoadCode.NIFTY_MONTHLY, 0.5))
    assert outcomes(classify(decisions, always(), 1))[0][:2] == (RoadCode.NIFTY_MONTHLY, Outcome.TRADE)


def test_a_refused_trade_frees_its_place_for_the_next_ranked_rule():
    def check(decision, accepted):
        return (refused(RefusalReason.MAX_LOSS),) if decision.road == RoadCode.BANKNIFTY_MONTHLY else (PASS,)

    decisions = (fired(RoadCode.BANKNIFTY_MONTHLY, 0.9), fired(RoadCode.NIFTY_MONTHLY, 0.1))
    assert outcomes(classify(decisions, check, 1)) == [
        (RoadCode.BANKNIFTY_MONTHLY, Outcome.REFUSED, RefusalReason.MAX_LOSS),
        (RoadCode.NIFTY_MONTHLY, Outcome.TRADE, "")]  # fmt: skip


def test_each_check_sees_the_trades_already_accepted_this_slot():
    seen = []

    def bucket(decision, accepted):  # a Rs 30,000 bucket of Rs 10,000 trades: the fourth breaks it
        seen.append(len(accepted))
        total = sum(d.proposal.max_loss for d in accepted) + decision.proposal.max_loss
        return (PASS,) if total <= 30_000 else (refused(RefusalReason.BUCKET_CAP),)

    monthlies = (RoadCode.NIFTY_MONTHLY, RoadCode.BANKNIFTY_MONTHLY, RoadCode.FINNIFTY_MONTHLY,
                 RoadCode.MIDCPNIFTY_MONTHLY)  # fmt: skip
    decisions = tuple(fired(road, 0.5, 10_000) for road in monthlies)
    classified = classify(decisions, bucket, 5)
    assert seen == [0, 1, 2, 3]
    assert [d.outcome for d, _ in classified] == [Outcome.TRADE] * 3 + [Outcome.TICKET]
    assert classified[-1][0].reason == TicketReason.ACCOUNT_LIMIT


@pytest.mark.parametrize("caps", [(RefusalReason.OPEN_RISK,), (RefusalReason.BUCKET_CAP, RefusalReason.MARGIN_ROOM),
                                  (RefusalReason.NEW_RISK_DAY,)])  # fmt: skip
def test_a_rule_refused_only_by_account_limits_becomes_an_account_limit_ticket(caps):
    [(out, results)] = classify((fired(RoadCode.NIFTY_MONTHLY, 0.5),), always(PASS, *map(refused, caps)), 5)
    assert (out.outcome, out.reason) == (Outcome.TICKET, TicketReason.ACCOUNT_LIMIT) and len(results) == 1 + len(caps)


@pytest.mark.parametrize("results, reason", [
    ((refused(RefusalReason.DAILY_STOP),), RefusalReason.DAILY_STOP),  # a stopped driver issues no ticket
    ((refused(RefusalReason.OPEN_RISK), refused(RefusalReason.BRAKE)), RefusalReason.BRAKE),  # nor a braked one: the
    # stop is named first, so a report shows why the driver stopped (judge 481 minor b)
    ((refused(RefusalReason.MAX_LOSS), refused(RefusalReason.DAILY_STOP)), RefusalReason.DAILY_STOP),
    ((refused(RefusalReason.BUCKET_CAP), refused(RefusalReason.MISSING_QUOTE)), RefusalReason.BUCKET_CAP),
    ((refused(RefusalReason.MAX_LOSS), refused(RefusalReason.OPEN_RISK)), RefusalReason.MAX_LOSS)])  # fmt: skip
def test_any_other_refusal_stays_refused_with_the_first_reason(results, reason):
    [(out, _)] = classify((fired(RoadCode.NIFTY_MONTHLY, 0.5),), always(*results), 5)
    assert (out.outcome, out.reason) == (Outcome.REFUSED, reason) and out.proposal is not None


def test_a_ticket_never_enters_the_slot_s_running_view():
    seen = {}

    def check(decision, accepted):  # the top rule breaks an account cap; the next one is a valid trade
        seen[decision.road] = accepted
        return (refused(RefusalReason.BUCKET_CAP),) if decision.road == RoadCode.BANKNIFTY_MONTHLY else (PASS,)

    decisions = (fired(RoadCode.BANKNIFTY_MONTHLY, 0.9), fired(RoadCode.NIFTY_MONTHLY, 0.1))
    classified = classify(decisions, check, 1)
    assert [(d.outcome, d.reason) for d, _ in classified] == [(Outcome.TICKET, TicketReason.ACCOUNT_LIMIT),
                                                             (Outcome.TRADE, "")]  # fmt: skip
    assert seen[RoadCode.NIFTY_MONTHLY] == (), "the ticket took no place and added no risk"


def test_a_rule_beyond_the_limit_that_breaks_a_binding_law_is_refused_not_ticketed():
    decisions = (fired(RoadCode.NIFTY_MONTHLY, 0.9), fired(RoadCode.BANKNIFTY_MONTHLY, 0.1))

    def check(decision, accepted):
        return (refused(RefusalReason.UNPROTECTED),) if accepted else (PASS,)

    assert [d.outcome for d, _ in classify(decisions, check, 1)] == [Outcome.TRADE, Outcome.REFUSED]


def test_only_fired_trades_are_classified():
    with pytest.raises(ValueError):
        classify((as_ticket(fired(RoadCode.NIFTY_MONTHLY, 0.5), TicketReason.TRADE_LIMIT),), always(), 5)


@pytest.mark.parametrize("reason", sorted(ACCOUNT_LIMITS))
def test_a_ticket_ignores_each_account_limit(reason):
    assert ticket_laws_pass((PASS, refused(reason))) and first_binding_refusal((PASS, refused(reason))) is None


@pytest.mark.parametrize("reason", sorted(set(RefusalReason) - ACCOUNT_LIMITS))
def test_a_ticket_obeys_every_other_law(reason):
    assert not ticket_laws_pass((PASS, refused(reason)))
    assert first_binding_refusal((refused(RefusalReason.OPEN_RISK), refused(reason))) == reason


def test_a_ticket_is_one_lot():
    decision = fired(RoadCode.NIFTY_MONTHLY, 0.5)
    two = replace(decision.proposal, legs=tuple(LegSpec(leg.key, leg.side, 2) for leg in decision.proposal.legs))
    with pytest.raises(ValueError):
        as_ticket(replace(decision, proposal=two), TicketReason.TRADE_LIMIT)
