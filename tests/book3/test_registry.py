"""Story D5 criteria 1, 2, 5 and 8 on a temporary git repository: a strategy is usable only when its row and spec are
committed before the decision, proposed on an earlier session, its spec unchanged and the registry never edited;
every registration enters the research ledger's Book 3 trial family."""

import subprocess
from datetime import date

import pytest

from fno.book3.registry import REGISTRY_FILE, TRIAL_FAMILY, NotRegistered, Provenance, RegistrationRefused, spec_path
from fno.research_engine.ledger import Ledger
from tests.book3.builders import PROVENANCE, commit, constitution, git, init_repo, registry, spec_text

PROPOSED, NEXT = date(2026, 11, 2), date(2026, 11, 3)


@pytest.fixture
def repo(tmp_path):
    init_repo(tmp_path)
    return tmp_path


def registered(repo, **spec):
    row = registry(repo).register(spec_text(**spec), PROVENANCE, constitution())
    return row, commit(repo, f"register {row['strategy_id']}")


def test_a_registration_dates_itself_from_the_clock_and_enters_the_trial_family(repo):
    row, _ = registered(repo)
    assert row["proposed_on"] == "2026-11-02" and row["strategy_id"] == "b3-sc-v1"
    assert (repo / spec_path("b3-sc-v1")).is_file()
    assert [r["trial_id"] for r in Ledger(repo).rows() if r["experiment"] == TRIAL_FAMILY] == ["book3:b3-sc-v1"]


def test_two_variants_both_count_in_the_trial_family_review_130(repo):
    """Criterion 8: a variant chosen after the market data is never a single trial."""
    registered(repo, name="b3-a")
    registered(repo, name="b3-b")
    family = [r for r in Ledger(repo).rows() if r["experiment"] == TRIAL_FAMILY]
    assert len(family) == 2


def test_a_strategy_is_usable_from_the_next_session_once_committed(repo):
    _, at = registered(repo)
    assert registry(repo).require_registered("b3-sc-v1", NEXT, at).key == ("b3-sc", 1)


def test_the_same_session_or_an_uncommitted_registration_is_refused(repo):
    """Criterion 1: no same-day invent-and-trade; a row not yet committed at the decision's commit does not count."""
    _, at = registered(repo)
    with pytest.raises(NotRegistered, match="not before"):
        registry(repo).require_registered("b3-sc-v1", PROPOSED, at)
    registry(repo).register(spec_text(name="b3-late"), PROVENANCE, constitution())  # written, not committed
    with pytest.raises(NotRegistered, match="not registered in a commit"):
        registry(repo).require_registered("b3-late-v1", NEXT, at)


def test_a_spec_edited_after_registration_is_refused(repo):
    """Criterion 2, edited on disk and edited in a later commit."""
    _, at = registered(repo)
    path = repo / spec_path("b3-sc-v1")
    path.write_text(path.read_text().replace("sc-test", "sc-test-edited") + "\n# edited\n")
    with pytest.raises(NotRegistered, match="differs"):
        registry(repo).require_registered("b3-sc-v1", NEXT, at)
    later = commit(repo, "edit the spec")
    with pytest.raises(NotRegistered, match="differs"):
        registry(repo).require_registered("b3-sc-v1", NEXT, later)


def test_an_edited_registry_row_is_refused_from_git_history(repo):
    """Criterion 5: a committed edit of an earlier row is found by comparing every committed version."""
    registered(repo)
    path = repo / REGISTRY_FILE
    path.write_text(path.read_text().replace("model-x", "model-y"))
    edited = commit(repo, "rewrite a row")
    assert registry(repo).edited_rows() == ["b3-sc-v1"]
    with pytest.raises(NotRegistered, match="edited, not appended"):
        registry(repo).require_registered("b3-sc-v1", NEXT, edited)


def test_a_spec_outside_the_constitution_a_repeat_or_an_unknown_parent_is_refused_at_registration(repo):
    """Criterion 3 at registration; a change is a new strategy_id, never a second row for the same one."""
    with pytest.raises(RegistrationRefused, match="not in the constitution"):
        registry(repo).register(spec_text(code="BF"), PROVENANCE, constitution(structures=["SC"]))
    registered(repo)
    with pytest.raises(RegistrationRefused, match="already registered"):
        registry(repo).register(spec_text(), PROVENANCE, constitution())
    with pytest.raises(RegistrationRefused, match="supersedes"):
        registry(repo).register(spec_text(name="b3-x"), Provenance("m", "p", "r", "new", "nope-v1"), constitution())


def parallel_registrations(repo):
    """Judge 263's history: from a base with one row, line A registers one strategy and line B another."""
    registered(repo, name="b3-x")
    main = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    git(repo, "checkout", "-qb", "line-b")
    registered(repo, name="b3-b")
    git(repo, "checkout", "-q", main)
    registered(repo, name="b3-a")


def merge_line_b(repo, keep) -> str:
    """Merges line B; each conflicted file becomes `keep(ours, theirs)` of its two sides' lines."""
    subprocess.run(["git", "merge", "-q", "--no-edit", "line-b"], cwd=repo, capture_output=True)
    for path in git(repo, "diff", "--name-only", "--diff-filter=U").split():
        ours, theirs = (git(repo, "show", f":{side}:{path}").splitlines() for side in (2, 3))
        (repo / path).write_text("\n".join(keep(ours, theirs)) + "\n")
    return commit(repo, "merge line B")


def both(ours, theirs):
    return ours + [line for line in theirs if line not in ours]


def test_two_registrations_on_parallel_lines_merged_with_both_rows_are_appends_judge_263(repo):
    parallel_registrations(repo)
    at = merge_line_b(repo, both)
    assert registry(repo).edited_rows() == []
    for strategy_id in ("b3-x-v1", "b3-a-v1", "b3-b-v1"):
        assert registry(repo).require_registered(strategy_id, NEXT, at).name == strategy_id[:-3]


def test_a_merge_that_drops_a_side_s_row_is_refused_judge_263(repo):
    parallel_registrations(repo)
    at = merge_line_b(repo, lambda ours, theirs: ours)  # B's row dropped in the merge
    assert registry(repo).edited_rows() == ["b3-b-v1"]
    with pytest.raises(NotRegistered, match="edited, not appended"):
        registry(repo).require_registered("b3-a-v1", NEXT, at)


def test_a_merge_that_edits_a_row_is_refused_judge_263(repo):
    parallel_registrations(repo)
    at = merge_line_b(repo, lambda ours, theirs: [line.replace("model-x", "model-y") for line in both(ours, theirs)])
    assert set(registry(repo).edited_rows(at)) == {"b3-x-v1", "b3-a-v1", "b3-b-v1"}


def test_a_shallow_clone_is_refused_since_its_history_checks_cannot_see_everything(repo, tmp_path_factory):
    registered(repo, name="b3-x")
    at = registered(repo, name="b3-y")[1]
    clone = tmp_path_factory.mktemp("shallow") / "clone"
    git(repo.parent, "clone", "-q", "--depth", "1", repo.as_uri(), str(clone))
    with pytest.raises(NotRegistered, match="shallow clone"):
        registry(clone).require_registered("b3-y-v1", NEXT, at)
