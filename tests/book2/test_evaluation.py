"""Story F5 part 1-3 (owner's Q11, Q12 (A) as the assumption pending the owner): Book 2's D2 evaluation. The no-trade
threshold binds Book 2's `paper` versions only, so a registered research candidate Book 2 may trade is allocated as
D2's shadow test allocates it; a pick's changed width or lots is rebuilt by D2's own `CandidateBuilder.at_terms`; a
stored run's picks give the same evaluation again."""

from fno.book2.evaluation import Book2Evaluators, binds_paper
from fno.constants import Decision
from fno.playbook.book2_playbook import Book2Playbook
from fno.playbook.selection import Pick
from tests.playbook.evaluation_builders import (
    DAY,
    EXPIRY,
    Counts,
    FixedValues,
    OwnShadowBooks,
    chain_market,
    evaluator,
    playbook,
    strategy,
)  # fmt: skip
from tests.risk.builders import book

RESEARCH = strategy("sc-research", "research", expected="none")
LOSING_PAPER = strategy("sc-paper", expected=-50.0)
R, P = f"sc-research-v1:{EXPIRY.isoformat()}", f"sc-paper-v1:{EXPIRY.isoformat()}"


def evaluators():
    rules = evaluator()
    return Book2Evaluators(rules.finder, rules.builder, rules.allocator, rules.real)


def evaluate(rule_evaluator, *strategies):
    base = playbook(*strategies, registered=[s.key for s in strategies if s.status == "research"])
    view = Book2Playbook(base.strategies, base.rows)
    evaluation = rule_evaluator.evaluate(DAY, view, chain_market(), FixedValues(), book(), Counts(), OwnShadowBooks())
    return {o.opportunity.opportunity_id: o for o in evaluation.outcomes}


def test_the_threshold_binds_paper_versions_only():
    outcomes = evaluate(evaluators().rule_default(), RESEARCH, LOSING_PAPER)
    assert outcomes[R].decision == Decision.CHOSEN  # no tested estimate, yet Book 2 may trade it (Q11)
    assert outcomes[P].decision == Decision.NO_TRADE and "no-trade threshold" in outcomes[P].reason


def test_binds_paper_reads_the_version_s_own_status():
    outcomes = evaluate(evaluators().rule_default(), RESEARCH, LOSING_PAPER)
    assert (binds_paper(outcomes[R].candidate), binds_paper(outcomes[P].candidate)) == (False, True)


def test_a_picked_paper_version_below_the_threshold_is_still_refused():
    rule_evaluator, _ = evaluators().with_picks([Pick(P, "AI likes it")], chain_market())
    assert evaluate(rule_evaluator, LOSING_PAPER)[P].decision == Decision.NO_TRADE


def test_a_changed_width_and_fewer_lots_are_rebuilt_by_d2():
    default = evaluate(evaluators().rule_default(), RESEARCH)[R].candidate.proposal.terms
    rule_evaluator, selection = evaluators().with_picks([Pick(R, "narrower", width=50.0, lots=1)], chain_market())
    chosen = evaluate(rule_evaluator, RESEARCH)[R]
    assert default.width == 100 and chosen.decision == Decision.CHOSEN and selection.attempted == []
    assert (chosen.candidate.proposal.terms.width, chosen.candidate.max_loss < 10_000) == (50, True)


def test_a_wider_pick_above_the_loss_cap_is_refused_by_d2_s_own_cap():
    rule_evaluator, selection = evaluators().with_picks([Pick(R, "wider", width=200.0)], chain_market())
    assert evaluate(rule_evaluator, RESEARCH)[R].decision == Decision.NOT_CHOSEN
    assert [a.why for a in selection.attempted] == [
        "rebuild refused: 200 x 1: maximum loss 10588.50 above the cap 10000"
    ]


def test_a_width_that_cannot_be_built_is_never_traded_and_is_attempted():
    rule_evaluator, selection = evaluators().with_picks([Pick(R, "odd", width=7.0)], chain_market())
    assert evaluate(rule_evaluator, RESEARCH)[R].decision == Decision.NOT_CHOSEN
    ((attempt,),) = [selection.attempted]
    assert attempt.why == "rebuild refused: 7 x 1: not listed with valid quotes"


def test_a_stored_run_s_picks_give_the_same_evaluation_again():
    picks = [Pick(R, "narrower", width=50.0)]
    first = evaluate(evaluators().with_picks(picks, chain_market())[0], RESEARCH)
    again = evaluate(evaluators().from_stored([p.to_json() for p in picks], chain_market()), RESEARCH)
    assert {k: o.record() for k, o in first.items()} == {k: o.record() for k, o in again.items()}


def test_no_picks_chooses_nothing():
    rule_evaluator, _ = evaluators().with_picks([], chain_market())
    assert {o.decision for o in evaluate(rule_evaluator, RESEARCH, LOSING_PAPER).values()} != {Decision.CHOSEN}
