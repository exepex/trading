"""Judge 85 addendum 1, should-fix: a frozen target deleted or renamed after the freeze is a change. `verify` names it,
and `version_of` refuses to count a decision whose commit no longer holds it."""

import pytest

from fno.evaluation.order import ChangedAfterFreeze, verify, version_of
from fno.playbook.history import PlaybookGit
from tests.evaluation.builders import protocol_repo
from tests.evaluation.test_order import decide, freeze
from tests.playbook.builders import commit_all, git

SCORING = "fno/scoring.py"


@pytest.mark.parametrize("how", ["deleted", "renamed"])
def test_a_frozen_target_deleted_or_renamed_is_refused(tmp_path, how):
    protocol_repo(tmp_path)
    freeze(tmp_path)
    if how == "deleted":
        git(tmp_path, "rm", "-q", SCORING)
    else:
        git(tmp_path, "mv", SCORING, "fno/scoring_v2.py")
    commit_all(tmp_path, f"frozen target {how}")
    after = decide(tmp_path, "book1_rules", "2026-11-02")
    assert verify(tmp_path) == [f"v1: {SCORING} changed after the freeze (a change is a new version)"]
    with pytest.raises(ChangedAfterFreeze, match=f"holds v1's frozen {SCORING} changed"):
        version_of(tmp_path, PlaybookGit(tmp_path), after)


def test_a_frozen_config_section_removed_is_refused(tmp_path):
    protocol_repo(tmp_path)
    freeze(tmp_path)
    config = tmp_path / "config.yaml"
    config.write_text(config.read_text().replace("scorecard_review:\n  confidence: 0.95\n", ""))
    commit_all(tmp_path, "frozen config section removed")
    after = decide(tmp_path, "book1_rules", "2026-11-02")
    assert verify(tmp_path) == ["v1: config.yaml:scorecard_review changed after the freeze (a change is a new version)"]
    with pytest.raises(ChangedAfterFreeze, match="config.yaml:scorecard_review"):
        version_of(tmp_path, PlaybookGit(tmp_path), after)
