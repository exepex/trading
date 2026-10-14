"""Story D1 criteria 1-2, 4-6 through the loader: duplicates, the registered fingerprint, status, evidence and the
live-feature gate; an empty playbook is valid and approves nothing."""

from datetime import date

import pytest

from fno.config import ROOT
from fno.constants import PlaybookStatus
from fno.playbook.fields import PlaybookError
from fno.playbook.registry import RegistryRow
from fno.playbook.schema import parse_strategy
from fno.playbook.wiring import build_playbook_loader

from .builders import (
    DOCUMENT,
    LIVE_FEATURES,
    FixedReports,
    changer,
    commit_all,
    document,
    filled_evidence,
    git,
    loader,
    report,
    repository,
    write,
)

DAY = date(2026, 10, 21)
F1_LIVE, F3_LIVE = LIVE_FEATURES


def refused(root, reports=None) -> PlaybookError:
    with pytest.raises(PlaybookError) as refusal:
        loader(root, reports).load()
    return refusal.value


def register(root, status, doc=None, evidence_commit="", by="owner", on=DAY):
    strategy = parse_strategy(doc or document())
    row = RegistryRow(strategy.name, strategy.version, strategy.parameters_sha256, status, on, by, evidence_commit)
    loader(root).registry.append(row)


def approved_repository(tmp_path, **changes) -> str:
    """A repository with an approved (paper) sc-test v1 whose evidence is committed; returns the approval commit."""
    results = repository(tmp_path)
    doc = document(evidence=filled_evidence(results), **changes)
    write(tmp_path / "playbook", doc)
    approval = commit_all(tmp_path, "evidence filled")
    register(tmp_path, "paper", doc=doc, evidence_commit=approval)
    path = tmp_path / "playbook" / "sc-test-v1.yaml"
    path.write_text(path.read_text().replace("status: research", "status: paper"))
    return approval


def test_an_empty_playbook_is_valid_and_approves_nothing(tmp_path):
    playbook = loader(tmp_path).load()
    assert playbook.strategies == () and playbook.approved() == ()


def test_two_files_with_the_same_name_and_version_are_refused(tmp_path):
    write(tmp_path / "playbook", document())
    write(tmp_path / "playbook", document(), "copy.yaml")
    refusal = refused(tmp_path)
    assert "copy.yaml" in refusal.field and "sc-test-v1.yaml" in refusal.field


def test_a_file_named_unlike_its_name_and_version_is_refused(tmp_path):
    write(tmp_path / "playbook", document(), "sc-test-v2.yaml")
    assert refused(tmp_path).field == "sc-test-v2.yaml"


def test_a_bad_file_is_refused_with_its_name_and_field(tmp_path):
    doc = document()
    doc["structure"]["code"] = "ZZ"
    write(tmp_path / "playbook", doc)
    assert refused(tmp_path).field == "sc-test-v1.yaml: structure.code"


def test_a_changed_parameter_in_a_registered_version_is_refused(tmp_path):
    path = write(tmp_path / "playbook", document())
    register(tmp_path, "research")
    assert loader(tmp_path).load().get("sc-test", 1).status == "research"
    path.write_text(path.read_text().replace("threshold: 0\n", "threshold: 0.5\n"))
    refusal = refused(tmp_path)
    assert refusal.field == "sc-test-v1.yaml: rule" and "new version" in str(refusal)


def test_a_comment_or_spacing_edit_is_not_a_parameter_change(tmp_path):
    path = write(tmp_path / "playbook", document())
    register(tmp_path, "research")
    path.write_text("# a note\n" + path.read_text().replace("name: sc-test", "name:    sc-test"))
    assert loader(tmp_path).load().get("sc-test", 1).status == "research"


def test_the_file_status_must_match_the_registry(tmp_path):
    write(tmp_path / "playbook", document(status="paused"))
    assert refused(tmp_path).field == "sc-test-v1.yaml: status"
    write(tmp_path / "playbook", document())
    register(tmp_path, "research")
    register(tmp_path, "retired")
    assert refused(tmp_path).field == "sc-test-v1.yaml: status"


def test_an_unregistered_paper_file_is_refused(tmp_path):
    write(tmp_path / "playbook", document(status="paper", evidence=filled_evidence("abcdef1")))
    assert refused(tmp_path).field == "sc-test-v1.yaml: status"


def test_a_registered_version_without_its_file_is_refused(tmp_path):
    write(tmp_path / "playbook", document())
    register(tmp_path, "research", doc=document(name="gone"))
    assert refused(tmp_path).field == "gone v1"


def test_an_approved_version_with_committed_evidence_and_validated_features_loads(tmp_path):
    approved_repository(tmp_path)
    assert [s.key for s in loader(tmp_path).load().approved()] == [("sc-test", 1)]


def test_paper_needs_every_evidence_field(tmp_path):
    approved_repository(tmp_path)
    path = tmp_path / "playbook" / "sc-test-v1.yaml"
    path.write_text(path.read_text().replace("owner_approval_date: 2026-10-20", "owner_approval_date: null"))
    assert refused(tmp_path).field == "sc-test-v1.yaml: evidence.owner_approval_date"


def test_evidence_changed_after_approval_is_refused(tmp_path):
    approved_repository(tmp_path)
    path = tmp_path / "playbook" / "sc-test-v1.yaml"
    path.write_text(path.read_text().replace("reviews/judge.md", "reviews/red_team.md"))
    assert refused(tmp_path).field == "sc-test-v1.yaml: evidence"


def drifted(root, reports) -> list[str]:
    """Judge 67 / E6: a paper version whose live feature fails is not approved and is listed as drifted (its pause is
    E6's), instead of refusing the whole load."""
    playbook = loader(root, reports).load()
    assert playbook.approved() == ()
    return [d.reason for d in playbook.drifted]


def test_a_live_feature_without_a_passing_report_takes_paper_away(tmp_path):
    approved_repository(tmp_path)
    only_f1 = FixedReports({F1_LIVE: report(F1_LIVE, 20)})
    assert "F3_live_scheduled_event_in_window" in drifted(tmp_path, only_f1)[0]
    f1_disagrees = FixedReports({F1_LIVE: report(F1_LIVE, 17), F3_LIVE: report(F3_LIVE, 20)})  # 85% < 90%
    [reason] = drifted(tmp_path, f1_disagrees)
    assert reason.startswith("sc-test-v1.yaml: entry_conditions") and F1_LIVE in reason


def test_the_gate_uses_the_strategys_own_stricter_rule(tmp_path):
    approved_repository(tmp_path, live_use_rule={"min_days": 20, "min_agreement": 0.95, "min_available": 0.9})
    at_90 = FixedReports({F1_LIVE: report(F1_LIVE, 18), F3_LIVE: report(F3_LIVE, 20)})  # passes B7's 90%, not 95%
    assert drifted(tmp_path, at_90)[0].startswith("sc-test-v1.yaml: entry_conditions")
    at_95 = FixedReports({F1_LIVE: report(F1_LIVE, 19), F3_LIVE: report(F3_LIVE, 20)})
    assert loader(tmp_path, at_95).load().approved()


def test_one_drifting_version_leaves_the_other_approved_versions_trading(tmp_path):
    approved_repository(tmp_path)
    other = document(name="sc-other", entry_conditions=[DOCUMENT["entry_conditions"][1]],
                     evidence=filled_evidence(git(tmp_path, "rev-parse", "HEAD~1")))  # fmt: skip
    write(tmp_path / "playbook", other)
    approval = commit_all(tmp_path, "second version")
    register(tmp_path, "paper", doc=other, evidence_commit=approval)
    path = tmp_path / "playbook" / "sc-other-v1.yaml"
    path.write_text(path.read_text().replace("status: research", "status: paper"))
    f1_disagrees = FixedReports({F1_LIVE: report(F1_LIVE, 17), F3_LIVE: report(F3_LIVE, 20)})
    playbook = loader(tmp_path, f1_disagrees).load()
    assert [s.name for s in playbook.approved()] == ["sc-other"]  # it uses only F3, which still agrees
    assert [d.strategy.name for d in playbook.drifted] == ["sc-test"]


def test_a_change_to_paper_with_an_unvalidated_feature_is_still_refused(tmp_path):
    results = repository(tmp_path)
    doc = document(evidence=filled_evidence(results))
    write(tmp_path / "playbook", doc)
    approval = commit_all(tmp_path, "evidence filled")
    only_f1 = FixedReports({F1_LIVE: report(F1_LIVE, 20)})
    with pytest.raises(PlaybookError, match="live features not validated"):
        changer(tmp_path, only_f1).change("sc-test", 1, PlaybookStatus.PAPER, "owner", DAY, approval)
    assert loader(tmp_path).registry.rows() == []


def test_the_repository_playbook_loads_and_approves_nothing():
    playbook = build_playbook_loader(ROOT).load()
    assert playbook.approved() == ()
    example = playbook.get("example-sc-iv-rich-no-event", 1)
    assert example.status == "research" and example.evidence.missing  # criterion 5: never a passed strategy
    assert "NOT A PASSED STRATEGY" in (ROOT / "playbook" / example.file_name).read_text()
