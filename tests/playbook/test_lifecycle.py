"""Story D1 criterion 3 end to end: a status change checks, appends one row and updates the file; a refused change
writes nothing."""

from datetime import date

import pytest

from fno.playbook.fields import PlaybookError

from .builders import FixedReports, changer, commit_all, document, filled_evidence, loader, repository, write

DAY = date(2026, 10, 21)


def candidate(tmp_path, evidence=True):
    results = repository(tmp_path)
    doc = document(evidence=filled_evidence(results)) if evidence else document()
    return write(tmp_path / "playbook", doc), commit_all(tmp_path, "candidate")


def snapshot(tmp_path, path):
    return (tmp_path / "playbook" / "registry.csv").read_text() if (
        tmp_path / "playbook" / "registry.csv"
    ).exists() else "", path.read_text()


def test_research_to_paper_to_paused_to_paper_to_retired(tmp_path):
    path, commit = candidate(tmp_path)
    steps = [("paper", "owner"), ("paused", "hard_loss_rule"), ("paper", "owner"), ("retired", "owner")]
    for status, by in steps:
        row = changer(tmp_path).change("sc-test", 1, status, by, DAY)
        assert loader(tmp_path).load().get("sc-test", 1).status == status
        assert f"status: {status}\n" in path.read_text()
    rows = loader(tmp_path).registry.rows()
    assert [r.status for r in rows] == [s for s, _ in steps] and rows[0].evidence_commit == commit
    assert row.evidence_commit == ""  # retiring needs no evidence commit


def test_the_owner_alone_may_resume_a_paused_strategy(tmp_path):
    path, _ = candidate(tmp_path)
    changer(tmp_path).change("sc-test", 1, "paper", "owner", DAY)
    changer(tmp_path).change("sc-test", 1, "paused", "owner", DAY)
    before = snapshot(tmp_path, path)
    with pytest.raises(PlaybookError):
        changer(tmp_path).change("sc-test", 1, "paper", "hard_loss_rule", DAY)
    assert snapshot(tmp_path, path) == before


@pytest.mark.parametrize(
    ("evidence", "reports", "field"),
    [
        (False, None, "sc-test-v1.yaml: evidence.test_results_path"),  # criterion 4
        (True, FixedReports({}), "sc-test-v1.yaml: entry_conditions"),  # criterion 6
    ],
)
def test_paper_is_refused_without_evidence_or_validated_features_and_nothing_is_written(
    tmp_path, evidence, reports, field
):
    path, _ = candidate(tmp_path, evidence)
    before = snapshot(tmp_path, path)
    with pytest.raises(PlaybookError) as refused:
        changer(tmp_path, reports).change("sc-test", 1, "paper", "owner", DAY)
    assert refused.value.field == field and snapshot(tmp_path, path) == before


def test_uncommitted_evidence_cannot_be_approved(tmp_path):
    path, _ = candidate(tmp_path, evidence=False)
    write(tmp_path / "playbook", document(evidence=filled_evidence("0" * 7)))
    with pytest.raises(PlaybookError) as refused:
        changer(tmp_path).change("sc-test", 1, "paper", "owner", DAY)
    assert refused.value.field.startswith("sc-test-v1.yaml: evidence")


def test_a_version_never_registered_cannot_be_changed(tmp_path):
    with pytest.raises(PlaybookError) as refused:
        changer(tmp_path).change("nothing", 1, "paper", "owner", DAY)
    assert refused.value.field == "nothing v1"


def test_the_desk_may_register_a_candidate_but_only_the_owner_approves_it(tmp_path):
    path, _ = candidate(tmp_path)
    changer(tmp_path).change("sc-test", 1, "research", "desk", DAY)
    assert loader(tmp_path).registry.rows()[0].approved_by == "desk"
    before = snapshot(tmp_path, path)
    with pytest.raises(PlaybookError) as refused:
        changer(tmp_path).change("sc-test", 1, "paper", "desk", DAY)
    assert refused.value.field == "approved_by" and snapshot(tmp_path, path) == before
    changer(tmp_path).change("sc-test", 1, "paper", "owner", DAY)
    assert loader(tmp_path).load().approved()[0].key == ("sc-test", 1)


def test_the_desk_cannot_approve_an_unregistered_candidate_either(tmp_path):
    path, _ = candidate(tmp_path)
    with pytest.raises(PlaybookError) as refused:
        changer(tmp_path).change("sc-test", 1, "paper", "desk", DAY)
    assert refused.value.field == "approved_by" and not (tmp_path / "playbook" / "registry.csv").exists()
