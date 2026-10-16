"""Story F6 criterion 12: the shared `SelectionAllocator` (Book 3 now, Book 2's F5 later). Only picks reach D2's
allocator (C2, the unproven limit, the threshold when on); every other candidate is "not chosen by <book>"; a pick
with width or lots needs a rebuild; picks that cannot trade are listed as attempted; C2's reasons stay D2's own."""

from dataclasses import replace

import pytest

from fno.constants import Decision
from fno.playbook.allocation import Allocator
from fno.playbook.candidates import NotBuilt
from fno.playbook.evaluate import RuleEvaluator
from fno.playbook.selection import NO_REBUILD, NOT_A_CANDIDATE, NOT_CHOSEN, Pick, SelectionAllocator
from fno.risk.inputs import TradeTerms
from fno.risk.manager import RiskManager
from fno.risk.rules import MaxLossPerTrade
from tests.playbook.evaluation_builders import (
    COSTS,
    DAY,
    EXPIRY,
    Counts,
    FixedValues,
    OwnShadowBooks,
    book_with_open,
    chain_market,
    evaluator,
    playbook,
    strategy,
)  # fmt: skip
from tests.risk.builders import book

A, B = f"sc-a-v1:{EXPIRY.isoformat()}", f"sc-b-v1:{EXPIRY.isoformat()}"


def run(picks, threshold=False, rebuild=None, max_open=3, the_book=None, expected=150.0, counts=None):
    rules = evaluator(max_open)
    selection = SelectionAllocator(rules.allocator, picks, "book_x", threshold, rebuild)
    evaluation = RuleEvaluator(rules.finder, rules.builder, selection, rules.real).evaluate(
        DAY, playbook(strategy("sc-a", expected=expected), strategy("sc-b", expected=expected)), chain_market(),
        FixedValues(), the_book or book(), counts or Counts(), OwnShadowBooks(),
    )  # fmt: skip
    return {o.opportunity.opportunity_id: o for o in evaluation.outcomes}, selection


def test_only_a_pick_is_chosen_and_the_rest_read_not_chosen_by_the_book_with_no_risk_verdict():
    outcomes, selection = run([Pick(A, "rich premium")])
    assert outcomes[A].decision == Decision.CHOSEN and outcomes[A].reason == "picked by book_x: rich premium"
    assert outcomes[A].risk is not None and outcomes[A].risk.ok
    assert (outcomes[B].decision, outcomes[B].reason, outcomes[B].risk) == (Decision.NOT_CHOSEN, NOT_CHOSEN.format(
        book="book_x"), None)  # fmt: skip
    assert selection.attempted == []


def test_no_pick_chooses_nothing():
    outcomes, _ = run([])
    assert {o.decision for o in outcomes.values()} == {Decision.NOT_CHOSEN}


def test_a_c2_refusal_keeps_d2_s_own_reason_text():
    outcomes, _ = run([Pick(A, "go")], max_open=1, the_book=book_with_open(1))
    assert outcomes[A].decision == Decision.NOT_CHOSEN and outcomes[A].reason.startswith("slot: ")


def test_the_threshold_is_the_book_s_own_setting():
    """Book 3 off (no tested estimate), Book 2 on: an expected net of `none` never trades with the threshold on."""
    assert run([Pick(A, "go")], threshold=False, expected="none")[0][A].decision == Decision.CHOSEN
    refused = run([Pick(A, "go")], threshold=True, expected="none")[0][A]
    assert refused.decision == Decision.NO_TRADE and "no-trade threshold" in refused.reason


def test_a_pick_with_width_or_lots_and_no_rebuild_is_refused_and_attempted():
    outcomes, selection = run([Pick(A, "narrower", width=100.0)])
    assert outcomes[A].decision == Decision.NOT_CHOSEN and outcomes[A].reason == NO_REBUILD.format(book="book_x")
    assert [(a.pick.opportunity_id, a.why) for a in selection.attempted] == [(A, NO_REBUILD.format(book="book_x"))]


def test_a_rebuild_is_checked_by_c2_and_a_failed_rebuild_is_attempted():
    def bigger(candidate, pick):
        terms = TradeTerms(candidate.proposal.terms.structure, candidate.proposal.terms.width, pick.lots)
        return replace(candidate, proposal=replace(candidate.proposal, terms=terms))

    outcomes, _ = run([Pick(A, "ten lots", lots=10)], rebuild=bigger)
    assert outcomes[A].candidate.proposal.terms.lots == 10  # the rebuilt candidate went to C2, over its loss cap
    assert outcomes[A].decision == Decision.NOT_CHOSEN and outcomes[A].reason.startswith("risk: ")

    def broken(candidate, pick):
        raise NotBuilt("no such width")

    outcomes, selection = run([Pick(A, "narrower", lots=1)], rebuild=broken)
    assert outcomes[A].reason == "rebuild refused: no such width"
    assert selection.attempted[0].why == "rebuild refused: no such width"


def test_a_pick_that_is_not_a_built_candidate_is_attempted_never_traded():
    outcomes, selection = run([Pick("sc-z-v1:2026-11-27", "invented"), Pick(A, "real")])
    assert outcomes[A].decision == Decision.CHOSEN
    assert [(a.pick.opportunity_id, a.why) for a in selection.attempted] == [("sc-z-v1:2026-11-27", NOT_A_CANDIDATE)]


def test_the_first_pick_of_an_id_wins():
    outcomes, _ = run([Pick(A, "first"), Pick(A, "second")])
    assert outcomes[A].reason == "picked by book_x: first"


def test_a_pick_round_trips_through_json():
    pick = Pick(A, "go", 200.0, 1)
    assert Pick.from_json(pick.to_json()) == pick
    assert Pick.from_json({"opportunity_id": A, "reason": "r"}) == Pick(A, "r")


@pytest.mark.parametrize("kept", [True, False])
def test_d2_s_allocator_is_the_one_that_ranks_and_checks(kept):
    """The selection never runs C2 itself: a manager refusing everything refuses the pick too."""
    risk = RiskManager((MaxLossPerTrade(COSTS, 10_000 if kept else 1),), {})
    rules = evaluator()
    selection = SelectionAllocator(Allocator(risk, COSTS), [Pick(A, "go")], "book_x", False)
    outcomes = RuleEvaluator(rules.finder, rules.builder, selection, rules.real).evaluate(
        DAY, playbook(strategy("sc-a")), chain_market(), FixedValues(), book(), Counts(), OwnShadowBooks()
    ).outcomes  # fmt: skip
    assert (outcomes[0].decision == Decision.CHOSEN) is kept


def test_book1_s_inputs_json_has_no_selection_or_opens_key_and_book3_s_keeps_both(tmp_path):
    """Book 1's stored bytes are unchanged by F6: the two keys appear only for an AI book's run."""
    from fno.playbook.decision_inputs import DayInputs, PlaybookSnapshot

    plain = DayInputs(DAY, PlaybookSnapshot({}, "", "c" * 40), {}).to_json()
    assert "selection" not in plain and "opens" not in plain["playbook"]
    with_picks = DayInputs(DAY, PlaybookSnapshot({}, "", "c" * 40, {}), {}, selection=(Pick(A, "go").to_json(),))
    stored = with_picks.to_json()
    assert stored["selection"] == [Pick(A, "go").to_json()] and stored["playbook"]["opens"] == {}
    assert DayInputs.from_json(stored) == with_picks
