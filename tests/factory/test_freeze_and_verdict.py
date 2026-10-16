"""G4 and G6 end to end (story R1c, criteria 8 and 10): freeze only a planned idea, judge once at the frozen sample by
Holm across the question's cumulative family, and never register a measurement."""

import math
from datetime import timedelta

import pytest

from fno.factory.constants import Gate
from fno.factory.gate_log import GateRow, figures
from fno.factory.gate_order import GateStepError
from fno.factory.registered_shadows import RegisteredShadows
from fno.factory.verdict import one_sided_p
from fno.factory.wiring import read_idea
from fno.research_engine.ledger import NotRegistered, write_ledger
from fno.scoreboard.uncertainty import holm

from .helpers import commit, git
from .shadow_helpers import (
    DAY,
    QUESTION,
    WINNING,
    Results,
    Versions,
    after_freeze,
    freezer,
    parts,
    planned_repo,
    verdicts,
)  # fmt: skip

ACCOUNT = "shadow:x1-sc-v1"


@pytest.fixture
def repo(tmp_path):
    return planned_repo(tmp_path)


def frozen(root):
    head = git(root, "rev-parse", "HEAD")
    row = freezer(root).freeze(read_idea("X1", root), DAY)
    commit(root, "freeze X1")
    return head, row


def test_freeze_names_the_protocol_commit_and_logs_the_registration(repo):
    head, row = frozen(repo)
    ledger = parts(repo)[1]
    assert ledger.rows()[-1]["protocol_commit"] == head
    ledger.require_registered("3")  # B4's guard accepts the frozen card
    assert (row.gate, row.outcome) == ("G4", "registered")
    assert figures(row) == {"version": "x1-sc-v1", "sample": "11", "pass_level": "0.05", "min_net": "150",
                            "question": QUESTION}  # fmt: skip
    shadow = RegisteredShadows(parts(repo)[0].gates).all()[0]
    assert (shadow.version, shadow.sample, shadow.minimum_useful_net) == ("x1-sc-v1", 11, 150.0)


def test_freeze_refuses_a_measurement_version_and_a_missing_one(repo):
    with pytest.raises(GateStepError, match="x1-sc-v1 is a measurement"):
        freezer(repo, Versions(measurements={("x1-sc", 1)})).freeze(read_idea("X1", repo), DAY)
    assert RegisteredShadows(parts(repo)[0].gates).all() == []  # criterion 10: never registered, never counted
    card = repo / "research/ideas/X1.md"
    card.write_text(card.read_text().replace("playbook_name: x1-sc", "playbook_name: missing"))
    commit(repo, "a version that does not exist")
    with pytest.raises(GateStepError, match="missing-v1 cannot be read"):
        freezer(repo).freeze(read_idea("X1", repo), DAY)


def test_freeze_refuses_a_pass_level_that_is_not_the_questions_alpha(tmp_path):
    repo = planned_repo(tmp_path)
    parts(repo)[3].add("other-question", "another", 0.01)
    card = repo / "research/ideas/X1.md"
    card.write_text(card.read_text().replace(f"question: {QUESTION}", "question: other-question"))
    commit(repo, "point at a 1% question")
    with pytest.raises(GateStepError, match="pass level 0.05 is not question 'other-question''s alpha 0.01"):
        freezer(repo).freeze(read_idea("X1", repo), DAY)


def test_a_verdict_waits_for_the_frozen_sample_and_is_given_once(repo):
    frozen(repo)
    with pytest.raises(GateStepError, match="10 of 11 positions, not at its frozen sample"):
        verdicts(repo, Results({ACCOUNT: WINNING[:10]})).judge(read_idea("X1", repo), DAY)
    result = verdicts(repo, Results({ACCOUNT: [*WINNING, -5000.0]})).judge(read_idea("X1", repo), DAY)
    assert result.passed and result.judged.p == pytest.approx(one_sided_p(WINNING))  # its first n positions only
    commit(repo, "verdict")
    with pytest.raises(GateStepError, match="its last gate is G6 passed"):
        verdicts(repo, Results({ACCOUNT: WINNING})).judge(read_idea("X1", repo), DAY)


def test_a_verdict_needs_a_committed_freeze(repo):
    freezer(repo).freeze(read_idea("X1", repo), DAY)  # not committed
    with pytest.raises(NotRegistered):
        verdicts(repo, Results({ACCOUNT: WINNING})).judge(read_idea("X1", repo), DAY)


def plant_family(root, others):
    gates = parts(root)[0].gates
    for n in range(others):
        numbers = f"version=other-v{n};sample=11;pass_level=0.05;min_net=150;question={QUESTION}"
        gates.append(GateRow(str(100 + n), Gate.REGISTRATION, "registered", "2026-10-17", "abc", numbers))
    commit(root, "nineteen more shadows on the question")


def test_the_survivor_of_twenty_never_passes_alone(repo):
    """Criterion 8: 19 shadows stopped short of their sample (p = 1) and one strong one; Holm at 5% across 20."""
    frozen(repo)
    plant_family(repo, 19)
    result = verdicts(repo, Results({ACCOUNT: WINNING})).judge(read_idea("X1", repo), DAY)
    assert len(result.members) == 20 and sum(m.p == 1.0 for m in result.members) == 19
    assert result.judged.p < 0.05 and not result.passed  # 0.0081 is above 0.05 / 20
    assert holm([0.004] + [1.0] * 19, 0.05) == [False] * 20 and holm([0.004], 0.05) == [True]


def test_an_earlier_verdict_is_never_relabelled(repo):
    frozen(repo)
    verdicts(repo, Results({ACCOUNT: WINNING})).judge(read_idea("X1", repo), DAY)
    commit(repo, "verdict X1")
    before = parts(repo)[0].gates.last("3")
    plant_family(repo, 19)
    assert parts(repo)[0].gates.last("3") == before and before.outcome == "passed"


def test_a_position_opened_on_or_before_the_freeze_day_never_counts(repo):
    """Judge 271, FACTORY_RULES section 3 rule 1: records made before the freeze never count."""
    frozen(repo)
    before = [(DAY - timedelta(days=i), 5000.0) for i in range(20)] + [(DAY, 5000.0)]
    results = Results({ACCOUNT: before})
    with pytest.raises(GateStepError, match="0 of 11 positions"):
        verdicts(repo, results).judge(read_idea("X1", repo), DAY)
    assert results.asked == [(ACCOUNT, DAY)]
    results = Results({ACCOUNT: before + after_freeze([-100.0] * 11)})
    result = verdicts(repo, results).judge(read_idea("X1", repo), DAY)
    assert result.judged.p == 1.0 and not result.passed and result.judged.opened_after == DAY.isoformat()
    assert figures(parts(repo)[0].gates.last("3"))["opened_after"] == DAY.isoformat()


def test_an_exploratory_trial_never_passes_but_stays_in_its_family(tmp_path):
    """Judge 271, FACTORY_RULES section 4: a test on spent or exposed data cannot pass G6."""
    repo = planned_repo(tmp_path, spent=True)
    assert parts(repo)[0].gates.last("3").outcome == "planned"
    frozen(repo)
    result = verdicts(repo, Results({ACCOUNT: WINNING})).judge(read_idea("X1", repo), DAY)
    assert result.holm_passed and result.exploratory and not result.passed
    row = parts(repo)[0].gates.last("3")
    assert (row.outcome, figures(row)["exploratory"]) == ("failed", "yes")
    assert len(result.members) == 1


def test_a_member_short_of_its_sample_enters_at_p_1_however_strong(repo):
    frozen(repo)
    plant_family(repo, 1)
    strong = [5000.0, 5200.0, 4900.0] * 3  # 9 strongly positive positions: short of the frozen 11
    result = verdicts(repo, Results({ACCOUNT: WINNING, "shadow:other-v0": strong})).judge(read_idea("X1", repo), DAY)
    other = next(m for m in result.members if m.version == "other-v0")
    assert one_sided_p(strong) < 0.001 and (other.positions, other.p) == (9, 1.0)


def test_the_p_value_matches_students_t_with_n_minus_1_degrees_of_freedom():
    """A known answer: nets 1..5, t = 3 / (sqrt(2.5) / sqrt(5)) = 4.2426 with 4 degrees of freedom; df 4 has the closed
    form F(t) = 1/2 + (3/8) u (1 - t^2 / (12 (1 + t^2 / 4))), u = t / sqrt(1 + t^2 / 4)."""
    t = 3 / (math.sqrt(2.5) / math.sqrt(5))
    u, x = t / math.sqrt(1 + t * t / 4), t * t / 4
    assert one_sided_p([1.0, 2.0, 3.0, 4.0, 5.0]) == pytest.approx(1 - (0.5 + 0.375 * u * (1 - x / (3 * (1 + x)))))
    assert one_sided_p([1.0, 2.0, 3.0, 4.0, 5.0]) == pytest.approx(0.0066178, abs=1e-7)


def test_a_trial_is_frozen_once(repo):
    frozen(repo)
    with pytest.raises(GateStepError, match="its last gate is G4 registered"):
        freezer(repo).freeze(read_idea("X1", repo), DAY)


def test_a_ledger_row_with_a_protocol_commit_is_never_frozen_again(repo):
    ledger = parts(repo)[1]
    rows = [r | {"protocol_commit": "abc123"} if r["trial_id"] == "3" else r for r in ledger.rows()]
    ledger.file.write_text(write_ledger(rows))
    commit(repo, "a commit set by hand")
    with pytest.raises(GateStepError, match="trial 3 is already frozen at abc123"):
        freezer(repo).freeze(read_idea("X1", repo), DAY)
