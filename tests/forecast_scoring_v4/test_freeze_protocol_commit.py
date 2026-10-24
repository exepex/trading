"""Story G6 freeze, criterion 2: the record's protocol commit is in the history and the protocol text at it is the one
the record pins (protocol section 10: "the commit that adds this text in its final form"). On a temporary repository."""

import hashlib
import subprocess

import pytest

from fno.forecast_scoring.v4 import freeze_check
from fno.research_engine.ledger import Git

PROTOCOL = freeze_check.PROTOCOL


def _git(root, *args):
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)
    return done.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.invalid")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "config", "core.hooksPath", "/dev/null")
    (tmp_path / PROTOCOL).parent.mkdir(parents=True)
    return tmp_path


def _commit(root, text: str, message: str) -> str:
    (root / PROTOCOL).write_text(text, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _record(commit: str, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"# Freeze\n\nProtocol commit: `{commit}`\n\n| File | SHA-256 |\n|---|---|\n| `{PROTOCOL}` | `{digest}` |\n"


def test_a_protocol_commit_in_the_history_with_the_pinned_text_holds(repo):
    commit = _commit(repo, "final text\n", "protocol")
    (repo / "FREEZE_v4.md").write_text("record", encoding="utf-8")  # a later commit that leaves the text alone
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "the record")
    assert freeze_check.protocol_problems(_record(commit, "final text\n"), Git(repo)) == []


def test_the_protocol_commit_equal_to_head_holds(repo):
    commit = _commit(repo, "final text\n", "protocol")
    assert freeze_check.protocol_problems(_record(commit, "final text\n"), Git(repo)) == []


def test_a_commit_outside_the_history_is_refused(repo):
    _commit(repo, "a\n", "first")
    _git(repo, "checkout", "-q", "-b", "side")
    side = _commit(repo, "final text\n", "side protocol")
    _git(repo, "checkout", "-q", "main")
    assert freeze_check.protocol_problems(_record(side, "final text\n"), Git(repo)) == [
        f"protocol commit {side[:10]} is not in this history"
    ]
    missing = "0" * 40
    assert freeze_check.protocol_problems(_record(missing, "a\n"), Git(repo)) == [
        f"protocol commit {missing[:10]} is not in this history"
    ]


def test_a_record_pinning_another_text_than_the_commits_is_refused(repo):
    commit = _commit(repo, "draft text\n", "protocol")
    assert freeze_check.protocol_problems(_record(commit, "final text\n"), Git(repo)) == [
        f"{PROTOCOL} at the protocol commit {commit[:10]} is not the text the record pins"
    ]


def test_a_record_without_or_with_two_protocol_commit_lines_is_refused(repo):
    commit = _commit(repo, "final text\n", "protocol")
    assert freeze_check.protocol_problems("# Freeze\n", Git(repo)) == [
        "the record has 0 'Protocol commit: `<40-hex sha>`' lines, not one"
    ]
    twice = _record(commit, "final text\n") + f"Protocol commit: `{commit}`\n"
    assert freeze_check.protocol_problems(twice, Git(repo)) == [
        "the record has 2 'Protocol commit: `<40-hex sha>`' lines, not one"
    ]


def test_an_earlier_commit_with_the_same_text_is_not_the_final_text_commit(repo):
    first = _commit(repo, "final text\n", "protocol")
    _commit(repo, "other\n", "an edit")
    _commit(repo, "final text\n", "the edit undone")
    assert freeze_check.protocol_problems(_record(first, "final text\n"), Git(repo)) == [
        f"protocol commit {first[:10]} is not the last commit that changed {PROTOCOL}"
    ]


def test_the_check_joins_the_files_and_the_protocol_commit(repo):
    commit = _commit(repo, "final text\n", "protocol")
    record = _record(commit, "final text\n")
    assert freeze_check.check(repo, record, Git(repo)) == freeze_check.FreezeCheck()
    _commit(repo, "edited text\n", "an edit after the freeze")
    found = freeze_check.check(repo, record, Git(repo))
    assert not found.holds() and found.problems == (
        f"{PROTOCOL}: changed since the freeze (a change is a new version, never an edit)",
        f"protocol commit {commit[:10]} is not the last commit that changed {PROTOCOL}",
    )


class ShallowGit(Git):
    def is_shallow(self) -> bool:
        return True


def test_a_shallow_clone_is_not_checked_never_broken_or_intact(repo):
    commit = _commit(repo, "final text\n", "protocol")
    found = freeze_check.check(repo, _record(commit, "final text\n"), ShallowGit(repo))
    assert not found.holds() and found.problems == () and found.lines()[0].startswith("v4 freeze NOT CHECKED: shallow")
