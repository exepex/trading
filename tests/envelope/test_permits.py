"""Story D4 criteria 1, 2, 3, 6 and 8: `AuthorityEnvelope.permits` over every envelope v1 action and status. The actions
a choice uses come from its terms against the rule default, never from a claim."""

import pytest

from fno.playbook.envelope import ActionStatus, AuthorityEnvelope, BookTerms, EnvelopeAction
from tests.envelope.builders import ALLOWED, FORBIDDEN, SHADOW, envelope, version

A = version("sc-a", lots=2, widths=(300, 200, 100))
B = version("sc-b", lots=1, widths=(250, 150))
DEFAULT = BookTerms(A.key, 300, 2)  # the rule's own trade on A: its widest width, its lots
ELIGIBLE = {A.key, B.key}


def permits(choice, statuses=None, b_statuses=None, rule_default=DEFAULT, eligible=ELIGIBLE, traded=None):
    envelopes = {A.key: envelope(A.key, **(statuses or {})), B.key: envelope(B.key, **(b_statuses or {}))}
    traded = traded or (B if choice and choice.version == B.key else A)
    return AuthorityEnvelope(envelopes).permits(choice, rule_default, traded, eligible)


@pytest.mark.parametrize(("choice", "action"), [
    (DEFAULT, EnvelopeAction.FOLLOW_RULE),
    (None, EnvelopeAction.NO_TRADE),
    (BookTerms(A.key, 200, 2), EnvelopeAction.CHOOSE_WIDTH),
    (BookTerms(A.key, 300, 1), EnvelopeAction.REDUCE_LOTS),
    (BookTerms(B.key, 250, 1), EnvelopeAction.CHOOSE_STRATEGY),
])  # fmt: skip
def test_each_action_is_derived_from_the_terms_and_follows_its_status(choice, action):
    assert permits(choice).actions == (action,) and permits(choice).allowed
    for status in (SHADOW, FORBIDDEN):
        on_b = choice is not None and choice.version == B.key
        verdict = permits(choice, b_statuses={action: status}) if on_b else permits(choice, {action: status})
        assert verdict.status == status


def test_an_action_absent_from_the_envelope_is_forbidden():
    assert permits(BookTerms(A.key, 200, 2), {"choose_width": None}).status == FORBIDDEN


def test_combined_actions_take_the_strictest_status():
    verdict = permits(BookTerms(A.key, 200, 1), {"choose_width": SHADOW})
    assert verdict.actions == (EnvelopeAction.CHOOSE_WIDTH, EnvelopeAction.REDUCE_LOTS) and verdict.status == SHADOW


@pytest.mark.parametrize(("choice", "why"), [
    (BookTerms(A.key, 300, 3), "size may only be reduced"),
    (BookTerms(A.key, 250, 2), "not in the version's set"),
    (BookTerms(A.key, 300, 0), "at least 1 lot"),
])  # fmt: skip
def test_a_lot_increase_or_a_width_outside_the_set_is_refused_whatever_the_envelope_says(choice, why):
    verdict = permits(choice)
    assert verdict.status == FORBIDDEN and why in verdict.reason


def test_no_eligible_version_leaves_only_follow_rule_and_no_trade():
    """Criterion 6: the rules offered no trade, so following them is no trade and any trade is refused."""
    assert permits(None, rule_default=None, eligible=set()).actions == (EnvelopeAction.FOLLOW_RULE,)
    assert permits(None, rule_default=None, eligible=set()).allowed
    trade = permits(BookTerms(A.key, 300, 2), rule_default=None, eligible=set())
    assert trade.status == FORBIDDEN and "never creates one" in trade.reason


def test_the_traded_version_s_envelope_governs_judge_207():
    """Criterion 8: A allows choose_width, B forbids it and allows choose_strategy. B at a width other than its own
    widest is refused; B at its own width passes."""
    b_rules = {"choose_width": FORBIDDEN, "choose_strategy": ALLOWED}
    assert permits(BookTerms(B.key, 150, 1), b_statuses=b_rules).status == FORBIDDEN
    assert permits(BookTerms(B.key, 250, 1), b_statuses=b_rules).allowed
    assert permits(BookTerms(B.key, 300, 1), b_statuses=b_rules).status == FORBIDDEN  # A's width: not in B's set


def test_an_ineligible_version_is_refused_review_130_point_3():
    """Criterion 9: A forbids choose_strategy, B allows it; B can be chosen only when it is eligible that day."""
    assert permits(BookTerms(B.key, 250, 1), {"choose_strategy": FORBIDDEN}).allowed
    refused = permits(BookTerms(B.key, 250, 1), {"choose_strategy": FORBIDDEN}, eligible={A.key})
    assert refused.status == FORBIDDEN and "not eligible" in refused.reason


def test_a_missing_envelope_is_forbidden():
    verdict = AuthorityEnvelope({}).permits(DEFAULT, DEFAULT, A, ELIGIBLE)
    assert verdict.status == ActionStatus.FORBIDDEN and "no trade envelope" in verdict.reason
