"""Story D2's acceptance criteria: one unmet condition stops the rule (1); with one free slot the higher expected net
per rupee of risk wins and the other is "not chosen: slot" (2); a negative expected net trades nothing (3); an
unproven version with an open trade gets no second one (4). Plus: research candidates are evaluated in shadow, never
in Book 1; nothing approved allocates nothing; the same inputs give the same record."""

import pytest

from fno.constants import Decision
from fno.risk.inputs import Proposal, TradeTerms
from fno.risk.rules import MaxLossPerTrade
from tests.risk.builders import book

from .builders import DOCUMENT
from .evaluation_builders import COSTS, LIVE_TRUE, Counts, OwnShadowBooks, book_with_open, chain_market, run, strategy


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
    full_shadow = OwnShadowBooks(books={"sc-new": book_with_open(3, name="shadow-sc-new")})
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
    return dict(DOCUMENT["structure"])


@pytest.mark.parametrize("wrong", ["book1_rules", "book2_hybrid", "book3_ai"])
def test_a_misconfigured_shadow_book_never_draws_on_a_real_account(wrong):
    """Orchestrator, 14 Oct 2026: a shadow version can never use Book 1's (or any book's) account."""
    candidate = strategy("sc-new", status="research")
    misconfigured = OwnShadowBooks(books={"sc-new": book(name=wrong)})
    with_shadow = run([strategy("sc-a"), candidate], shadow=misconfigured, registered=[candidate.key])
    result = outcome(with_shadow, "sc-new")
    assert result.decision == Decision.SHADOW_NO_TRADE and result.risk is None and "real book" in result.reason
    alone = run([strategy("sc-a")])
    assert outcome(with_shadow, "sc-a").record() == outcome(alone, "sc-a").record()


def test_a_shadow_version_without_an_estimate_still_records_what_the_rule_would_do():
    candidate = strategy("sc-new", status="research", expected="none")
    result = outcome(run([candidate], registered=[candidate.key]), "sc-new")
    assert result.decision == Decision.SHADOW_TRADE and result.record()["trade"]["score"] is None


def test_the_no_trade_threshold_binds_paper_only_not_the_shadow():
    candidate = strategy("sc-new", status="research", expected=-50.0)
    assert outcome(run([candidate], registered=[candidate.key]), "sc-new").decision == Decision.SHADOW_TRADE
    assert outcome(run([strategy("sc-a", expected=-50.0)]), "sc-a").decision == Decision.NO_TRADE


def test_lots_whose_max_loss_breaks_the_cap_are_refused_never_trimmed():
    """Orchestrator, 14 Oct 2026: 3 lots of the 100-wide condor lose ~Rs 14,550 at most, above Rs 10,000."""
    heavy = strategy("sc-a", structure={**_structure(), "lots": 3})
    result = outcome(run([heavy]), "sc-a")
    assert result.decision == Decision.NO_TRADE and result.candidate is None
    assert "100: maximum loss" in result.reason and "above the cap 10000" in result.reason
    assert outcome(run([strategy("sc-a")]), "sc-a").record()["trade"]["lots"] == 1  # 1 lot of the same trade passes


def test_c2_refuses_the_same_oversized_trade_on_its_own():
    """The desk's width choice and C2's per-trade rule agree: C2 alone refuses the 3-lot trade too."""
    one_lot = outcome(run([strategy("sc-a")]), "sc-a").candidate.proposal
    three = Proposal(one_lot.trade_id, TradeTerms("SC", 100, 3), one_lot.lot_size, one_lot.legs)
    verdict = MaxLossPerTrade(COSTS, 10_000).check(three, book(), chain_market())
    assert not verdict.ok
