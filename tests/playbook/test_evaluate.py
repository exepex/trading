"""Story D2's acceptance criteria: one unmet condition stops the rule (1); with one free slot the higher expected net
per rupee of risk wins and the other is "not chosen: slot" (2); a negative expected net trades nothing (3); an
unproven version with an open trade gets no second one (4). Plus: research candidates are evaluated in shadow, never
in Book 1; nothing approved allocates nothing; the same inputs give the same record."""

import pytest

from fno.constants import Decision

from .evaluation_builders import LIVE_TRUE, Counts, OwnShadowBooks, book_with_open, run, strategy


def outcome(evaluation, name):
    return next(o for o in evaluation.outcomes if o.opportunity.strategy.name == name)


def test_all_conditions_true_fires_and_the_widest_width_within_the_cap_is_traded():
    evaluation = run([strategy("sc-a")])
    chosen = outcome(evaluation, "sc-a")
    assert chosen.decision == Decision.CHOSEN and evaluation.record()["chosen"] == [chosen.opportunity.opportunity_id]
    trade = chosen.record()["trade"]
    assert trade["width"] == 100 and 0 < trade["max_loss_rs"] <= 10_000  # 300 and 200 break the Rs 10,000 cap
    assert [leg["strike"] for leg in trade["legs"]] == [25_500, 24_500, 25_600, 24_400]


@pytest.mark.parametrize(
    ("feature", "value"),
    [
        ("F1_live_atm_iv_minus_rv20", -0.5),
        ("F1_live_atm_iv_minus_rv20", None),
        ("F3_live_scheduled_event_in_window", True),
    ],
)
def test_one_unmet_condition_stops_the_rule_and_is_recorded(feature, value):
    evaluation = run([strategy("sc-a")], values={**LIVE_TRUE, feature: value})
    result = outcome(evaluation, "sc-a")
    assert result.decision == Decision.NO_TRADE and result.reason == "rule did not fire"
    assert len(result.unmet) == 1 and result.unmet[0].startswith(feature)
    assert evaluation.record()["decision"] == "no trade"


def test_with_one_free_slot_the_better_expected_net_per_rupee_wins():
    evaluation = run([strategy("sc-low", expected=100), strategy("sc-high", expected=300)], the_book=book_with_open(2))
    assert outcome(evaluation, "sc-high").decision == Decision.CHOSEN
    loser = outcome(evaluation, "sc-low")
    assert loser.decision == Decision.NOT_CHOSEN and loser.reason.startswith("slot:")


def test_ranking_is_per_rupee_of_risk_not_raw_expected_net():
    wide = strategy("sc-wide", expected=200, structure={**_structure(), "widths": [100]})  # max loss ~ Rs 4,850
    narrow = strategy("sc-narrow", expected=150, structure={**_structure(), "widths": [50]})  # max loss ~ Rs 2,380
    evaluation = run([wide, narrow], the_book=book_with_open(2))
    assert outcome(evaluation, "sc-wide").candidate.score < outcome(evaluation, "sc-narrow").candidate.score
    assert outcome(evaluation, "sc-narrow").decision == Decision.CHOSEN
    assert outcome(evaluation, "sc-wide").decision == Decision.NOT_CHOSEN


def test_ties_go_to_the_strategy_name_when_score_loss_and_expiry_are_equal():
    evaluation = run([strategy("sc-b"), strategy("sc-a")], the_book=book_with_open(2))
    assert outcome(evaluation, "sc-a").decision == Decision.CHOSEN
    assert outcome(evaluation, "sc-b").decision == Decision.NOT_CHOSEN


@pytest.mark.parametrize("expected", [-50.0, 0.0])
def test_expected_net_not_above_zero_trades_nothing(expected):
    evaluation = run([strategy("sc-a", expected=expected)])
    result = outcome(evaluation, "sc-a")
    assert result.decision == Decision.NO_TRADE and "no-trade threshold" in result.reason
    assert evaluation.record()["decision"] == "no trade"


def test_an_unproven_strategy_with_an_open_trade_gets_no_second():
    evaluation = run([strategy("sc-a")], counts=Counts(completed=19, open_=1))
    result = outcome(evaluation, "sc-a")
    assert result.decision == Decision.NOT_CHOSEN and result.reason.startswith("unproven:")
    assert outcome(run([strategy("sc-a")], counts=Counts(completed=20, open_=1)), "sc-a").decision == Decision.CHOSEN
    assert outcome(run([strategy("sc-a")], counts=Counts(completed=0, open_=0)), "sc-a").decision == Decision.CHOSEN


def test_a_registered_research_candidate_is_evaluated_in_shadow_only():
    shadow = OwnShadowBooks()
    candidate = strategy("sc-new", status="research")
    evaluation = run([candidate], shadow=shadow, registered=[candidate.key])
    result = outcome(evaluation, "sc-new")
    assert result.opportunity.mode == "shadow" and result.decision == Decision.SHADOW_TRADE
    assert result.risk.book == "shadow-sc-new" and shadow.asked == [candidate.key]
    assert evaluation.chosen == () and evaluation.record()["decision"] == "no trade"  # nothing for Book 1


def test_shadow_and_book_never_share_slots():
    candidate = strategy("sc-new", status="research")
    full_shadow = OwnShadowBooks(books={"sc-new": book_with_open(3)})
    evaluation = run([strategy("sc-a"), candidate], shadow=full_shadow, registered=[candidate.key])
    assert outcome(evaluation, "sc-a").decision == Decision.CHOSEN  # Book 1's empty book has room
    shadow = outcome(evaluation, "sc-new")
    assert shadow.decision == Decision.SHADOW_NO_TRADE and shadow.reason.startswith("slot:")


def test_an_unregistered_candidate_is_not_tested():
    shadow = OwnShadowBooks()
    evaluation = run([strategy("sc-new", status="research")], shadow=shadow)
    assert evaluation.outcomes == () and shadow.asked == []


def test_nothing_approved_allocates_nothing():
    evaluation = run([])
    assert evaluation.record() == {"day": "2026-10-13", "book": "book1_rules", "decision": "no trade", "chosen": [],
                                   "outcomes": []}  # fmt: skip


def test_paused_and_retired_versions_are_not_evaluated():
    assert run([strategy("sc-a", status="paused"), strategy("sc-b", status="retired")]).outcomes == ()


def test_impossible_prices_are_a_validity_failure_not_a_trade():
    prices = {
        (k, kind): (500.0 if k in (25_500, 24_500) else 1.0) for k in range(24_000, 26_050, 50) for kind in ("CE", "PE")
    }
    result = outcome(run([strategy("sc-a")], prices=prices), "sc-a")
    assert result.decision == Decision.NO_TRADE and result.reason.startswith("validity:")


def test_no_width_within_the_cap_is_no_trade():
    result = outcome(run([strategy("sc-a", structure={**_structure(), "widths": [300, 200]})]), "sc-a")
    assert result.decision == Decision.NO_TRADE and "above the cap" in result.reason


def test_the_same_inputs_give_the_same_record():
    strategies = [strategy("sc-low", expected=100), strategy("sc-high", expected=300)]
    assert run(strategies, the_book=book_with_open(2)).record() == run(strategies, the_book=book_with_open(2)).record()


def _structure():
    from .builders import DOCUMENT

    return dict(DOCUMENT["structure"])
