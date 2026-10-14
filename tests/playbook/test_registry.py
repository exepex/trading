"""Story D1 criteria 2-3: the registry's allowed changes, one row per change, append-only (checked on git history)."""

from datetime import date

import pytest

from fno.config import ROOT
from fno.constants import PlaybookStatus
from fno.playbook.fields import PlaybookError
from fno.playbook.history import PlaybookGit
from fno.playbook.registry import Registry, RegistryRow, parse_rows, render, rewritten_history
from fno.playbook.transitions import ALLOWED, check_transition

from .builders import commit_all, git

SHA = "a" * 64
STATUSES = (None, *PlaybookStatus)
EXPECTED = {
    (None, "research"): {"owner", "desk"}, (None, "paper"): {"owner"}, (None, "retired"): {"owner"},
    ("research", "paper"): {"owner"}, ("research", "retired"): {"owner"},
    ("paper", "paused"): {"owner", "hard_loss_rule"}, ("paper", "retired"): {"owner"},
    ("paused", "paper"): {"owner"}, ("paused", "retired"): {"owner"},
}  # fmt: skip


def row(status, by="owner", on=date(2026, 10, 21), sha=SHA, evidence="abcdef1", name="s", version=1):
    return RegistryRow(name, version, sha, PlaybookStatus(status), on, by, evidence)


@pytest.mark.parametrize("before", STATUSES)
@pytest.mark.parametrize("after", list(PlaybookStatus))
@pytest.mark.parametrize("by", ["owner", "desk", "hard_loss_rule", "claude"])
def test_only_the_story_s_changes_are_allowed_and_only_by_their_approver(before, after, by):
    allowed = by in EXPECTED.get((before, after), set())
    if allowed:
        check_transition(before, after, by)
    else:
        with pytest.raises(PlaybookError):
            check_transition(before, after, by)


def test_the_table_has_no_change_beyond_the_story():
    assert {(b, a): set(who) for (b, a), who in ALLOWED.items()} == EXPECTED


def test_each_change_is_a_new_row_and_old_bytes_stay(tmp_path):
    registry = Registry(tmp_path / "registry.csv")
    registry.append(row("research", evidence=""))
    before = registry.path.read_text()
    registry.append(row("paper"))
    registry.append(row("paused", by="hard_loss_rule", evidence=""))
    assert registry.path.read_text().startswith(before)
    assert [r.status for r in registry.rows()] == ["research", "paper", "paused"]
    assert registry.latest()[("s", 1)].status == "paused"


@pytest.mark.parametrize(
    ("rows", "field"),
    [
        ([row("paused", evidence="")], "registry.csv s v1 status"),  # no paper before it
        ([row("paper"), row("paper", on=date(2026, 10, 22))], "registry.csv s v1 status"),  # not a change
        ([row("paper"), row("paused", sha="b" * 64)], "registry.csv s v1 sha256"),  # a changed rule
        ([row("paper"), row("paused", on=date(2026, 10, 1))], "registry.csv s v1 changed_on"),
        ([row("paper", evidence="")], "registry.csv line 2 evidence_commit"),
        ([row("paper", sha="short")], "registry.csv line 2 sha256"),
    ],
)
def test_a_bad_history_is_refused_with_its_place(rows, field):
    with pytest.raises(PlaybookError) as refused:
        parse_rows(render(rows))
    assert refused.value.field == field


def test_append_refuses_a_disallowed_change_and_writes_nothing(tmp_path):
    registry = Registry(tmp_path / "registry.csv")
    registry.append(row("paper"))
    before = registry.path.read_text()
    with pytest.raises(PlaybookError):
        registry.append(row("research", evidence=""))
    assert registry.path.read_text() == before


def test_wrong_columns_are_refused():
    with pytest.raises(PlaybookError):
        parse_rows("name,version\n")


def test_rewritten_history_finds_an_edited_past_row():
    first = render([row("paper")])
    second = render([row("paper"), row("retired", evidence="")])
    assert rewritten_history([first, second]) == []
    edited = second.replace("2026-10-21,owner,abcdef1", "2026-10-20,owner,abcdef1", 1)
    assert rewritten_history([first, edited]) == ["version 1 does not keep version 0's rows unchanged"]


def test_the_history_check_reads_git(tmp_path):
    git(tmp_path, "init", "-q")
    registry = Registry(tmp_path / "playbook" / "registry.csv")
    registry.path.parent.mkdir()
    registry.append(row("paper"))
    commit_all(tmp_path)
    registry.path.write_text(registry.path.read_text().replace("abcdef1", "abcdef2"))
    commit_all(tmp_path)
    versions = PlaybookGit(tmp_path).file_versions("playbook/registry.csv")
    assert len(versions) == 2 and rewritten_history(versions)


def test_the_repository_registry_was_only_ever_appended_to():
    versions = PlaybookGit(ROOT).file_versions("playbook/registry.csv")
    assert rewritten_history(versions) == []
    current = (ROOT / "playbook" / "registry.csv").read_text()
    assert not versions or current.startswith(versions[-1])  # uncommitted edits keep the committed rows too
    parse_rows(current)
