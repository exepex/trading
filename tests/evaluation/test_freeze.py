"""Story S1, criteria 1-3: the freeze records the protocol commit and the hashes of every listed file and config
section, and registers the protocol in the research ledger (B4). It refuses a protocol that is uncommitted, not
decided, lists a missing file, or is already frozen. Any later change to a hashed target is a new version."""

from datetime import date

import pytest

from fno.evaluation.freeze import (
    FreezeRefused,
    ProtocolFreezer,
    WorkingTree,
    changed_targets,
    freeze_path,
    frozen_targets,
    read_record,
    target_hash,
)  # fmt: skip
from fno.evaluation.gate import GATE_FILE
from fno.evaluation.protocol import PROTOCOL_FILE
from fno.playbook.history import PlaybookGit
from fno.research_engine.ledger import read_ledger
from tests.evaluation.builders import DRAFT, decided, protocol_repo, small_frozen_files
from tests.playbook.builders import commit_all

TODAY = date(2026, 10, 21)


def freezer(root) -> ProtocolFreezer:
    return ProtocolFreezer(root, PlaybookGit(root))


def test_the_freeze_records_the_protocol_commit_and_every_hash_and_registers_the_protocol(tmp_path):
    commit = protocol_repo(tmp_path)
    record = freezer(tmp_path).freeze(TODAY)
    assert record.version == 1 and record.protocol_commit == commit
    assert set(record.hashes) == {PROTOCOL_FILE, "fno/scoring.py", "config.yaml:desk.timetable",
                                  "config.yaml:scorecard_review", GATE_FILE}  # fmt: skip
    assert read_record((tmp_path / freeze_path(1)).read_text()) == record
    row = read_ledger((tmp_path / "research/ledger.csv").read_text())[-1]
    assert (row["trial_id"], row["experiment"], row["kind"], row["hypothesis"]) == (
        "2", "evaluation-protocol-v1", "prospective", "no",
    )  # fmt: skip
    assert (row["protocol_path"], row["protocol_commit"], row["registered_on"]) == (PROTOCOL_FILE, commit, "2026-10-21")


def test_a_draft_is_never_frozen(tmp_path):
    protocol_repo(tmp_path, small_frozen_files(DRAFT))
    with pytest.raises(FreezeRefused, match="not decided by the owner: common_start"):
        freezer(tmp_path).freeze(TODAY)
    assert not (tmp_path / freeze_path(1)).exists()


def test_a_decided_protocol_with_a_number_still_marked_for_the_freeze_day_is_never_frozen(tmp_path):
    """Judge 196: the cash rate's placeholder is refused until the owner sets it and removes the marker."""
    text = small_frozen_files(decided()).replace(
        "cash rate = 5.5% a year", "cash rate = 5.5% a year (set at the freeze)"
    )
    protocol_repo(tmp_path, text)
    with pytest.raises(FreezeRefused, match="not decided by the owner: do_nothing_benchmark"):
        freezer(tmp_path).freeze(TODAY)
    assert not (tmp_path / freeze_path(1)).exists()


def test_an_incomplete_protocol_is_never_frozen(tmp_path):
    protocol_repo(tmp_path, small_frozen_files(decided()).replace("Block length 20", "Block length to be decided"))
    with pytest.raises(FreezeRefused, match="to be decided"):
        freezer(tmp_path).freeze(TODAY)


def test_an_uncommitted_protocol_is_never_frozen(tmp_path):
    protocol_repo(tmp_path)
    (tmp_path / PROTOCOL_FILE).write_text((tmp_path / PROTOCOL_FILE).read_text() + "\nedited\n")
    with pytest.raises(FreezeRefused, match="commit research/evaluation/PROTOCOL.md first"):
        freezer(tmp_path).freeze(TODAY)


def test_a_listed_file_that_does_not_exist_refuses_the_freeze(tmp_path):
    protocol_repo(tmp_path, small_frozen_files(decided()).replace("`fno/scoring.py`", "`fno/scoreboard/a.py`"))
    with pytest.raises(FreezeRefused, match="fno/scoreboard/a.py is listed in frozen_files but does not exist"):
        freezer(tmp_path).freeze(TODAY)


def test_a_frozen_version_is_never_frozen_again(tmp_path):
    protocol_repo(tmp_path)
    freezer(tmp_path).freeze(TODAY)
    commit_all(tmp_path, "freeze")
    with pytest.raises(FreezeRefused, match="exists: a change is a new protocol version"):
        freezer(tmp_path).freeze(TODAY)


def test_a_change_to_any_hashed_target_shows_and_an_unrelated_setting_does_not(tmp_path):
    protocol_repo(tmp_path)
    record = freezer(tmp_path).freeze(TODAY)
    config = tmp_path / "config.yaml"
    config.write_text(config.read_text().replace("channel_id: C0", "channel_id: C1"))
    assert changed_targets(WorkingTree(tmp_path), record) == []  # not a frozen section
    config.write_text(config.read_text().replace('decision_deadline: "15:12"', 'decision_deadline: "15:13"'))
    (tmp_path / "fno/scoring.py").write_text("SCORE = 2\n")
    assert changed_targets(WorkingTree(tmp_path), record) == ["config.yaml:desk.timetable", "fno/scoring.py"]


def test_a_config_section_hash_ignores_layout_but_not_values(tmp_path):
    protocol_repo(tmp_path)
    before = target_hash(WorkingTree(tmp_path), "config.yaml:scorecard_review")
    config = tmp_path / "config.yaml"
    config.write_text(config.read_text().replace("  confidence: 0.95", "  confidence: 0.95   # a comment"))
    assert target_hash(WorkingTree(tmp_path), "config.yaml:scorecard_review") == before
    config.write_text(config.read_text().replace("0.95", "0.9"))
    assert target_hash(WorkingTree(tmp_path), "config.yaml:scorecard_review") != before
    with pytest.raises(FreezeRefused, match="no section 'desk.missing'"):
        target_hash(WorkingTree(tmp_path), "config.yaml:desk.missing")


def test_the_real_drafts_targets_include_every_listed_file():
    targets = frozen_targets(DRAFT)
    assert {PROTOCOL_FILE, "fno/scorecard/review.py", "fno/desk/timetable.py", "config.yaml:desk.timetable",
            "config.yaml:scorecard_review", "config.yaml:risk", "config.yaml:charges"} <= set(targets)  # fmt: skip


def test_the_freeze_names_the_last_commit_that_changed_the_protocol(tmp_path):
    protocol_repo(tmp_path)
    protocol = tmp_path / PROTOCOL_FILE
    protocol.write_text(protocol.read_text().replace("## Freezing", "## Freezing (as decided)"))
    latest = commit_all(tmp_path, "protocol edited before the freeze")
    assert freezer(tmp_path).freeze(TODAY).protocol_commit == latest


def test_the_protocol_is_always_a_target_even_when_not_listed():
    unlisted = small_frozen_files(decided()).replace("`research/evaluation/PROTOCOL.md`, ", "")
    assert "`research/evaluation/PROTOCOL.md`" not in unlisted[unlisted.index("### `frozen_files`") :]
    assert PROTOCOL_FILE in frozen_targets(unlisted)


@pytest.mark.parametrize(
    ("path", "edit"),
    [("fno/scoring.py", "SCORE = 2\n"), ("config.yaml", None)],
)
def test_a_listed_file_or_config_edited_since_head_refuses_the_freeze(tmp_path, path, edit):
    protocol_repo(tmp_path)
    target = tmp_path / path
    target.write_text(edit if edit is not None else target.read_text().replace("15:12", "15:13"))
    with pytest.raises(FreezeRefused, match=f"commit {path} first"):
        freezer(tmp_path).freeze(TODAY)
