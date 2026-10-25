"""Story GB1: the branch facts are read from real git, on a throw-away origin and clone."""

import os
import subprocess
import sys

import pytest

from fno.config import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import branch_git  # noqa: E402


def git(cwd, *args, date=None):
    env = {**os.environ, "GIT_COMMITTER_DATE": date} if date else None
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=cwd, capture_output=True, text=True, check=True, env=env,
    )  # fmt: skip
    return done.stdout.strip()


def commit(cwd, name, text="x"):
    (cwd / name).write_text(text)
    git(cwd, "add", name)
    git(cwd, "commit", "-q", "-m", name)


@pytest.fixture
def clone(tmp_path, monkeypatch):
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(tmp_path, "clone", "-q", str(origin), str(work))
    git(work, "checkout", "-q", "-b", "main")
    commit(work, "base")
    git(work, "push", "-q", "origin", "main")
    monkeypatch.setattr(branch_git, "ROOT", work)
    return work


def push_branch(work, name, files):
    git(work, "checkout", "-q", "-b", name, "main")
    for file in files:
        commit(work, file)
    git(work, "push", "-q", "origin", name)
    git(work, "checkout", "-q", "main")


def test_merged_unmerged_and_fresh_branches_are_told_apart(clone):
    push_branch(clone, "story/merged", ["a.txt"])
    git(clone, "merge", "-q", "--no-ff", "-m", "merge", "story/merged")
    git(clone, "push", "-q", "origin", "main")
    push_branch(clone, "story/open", ["b.txt", "c.txt"])
    git(clone, "branch", "story/fresh", "main")  # cut from main, nothing committed yet
    git(clone, "push", "-q", "origin", "story/fresh")
    git(clone, "fetch", "-q", "origin")

    found = {b.name: b for b in branch_git.read_branches()}

    assert found["story/merged"].merged and found["story/merged"].landed_at is not None
    assert not found["story/open"].merged and found["story/open"].ahead == 2
    assert found["story/fresh"].merged  # indistinguishable from a merged one: the keep list and the grace cover it
    assert "HEAD" not in found and found["main"].merged


def test_unfinished_code_is_counted_only_for_commits_not_on_main(clone):
    (clone / "fno").mkdir()
    push_branch(clone, "story/code", ["fno/new.py"])
    git(clone, "fetch", "-q", "origin")
    push_branch(clone, "story/docs", ["notes.md"])
    git(clone, "fetch", "-q", "origin")

    found = {b.name: b for b in branch_git.read_branches(with_code=True)}

    assert found["story/code"].code_files == 1 and found["story/docs"].code_files == 0


def test_remote_heads_read_the_origin_not_the_fetched_copies(clone):
    push_branch(clone, "story/x", ["a.txt"])
    heads = branch_git.remote_heads()
    assert heads["story/x"] == git(clone, "rev-parse", "story/x") and "story/none" not in heads


def test_open_pr_heads_ignores_blank_lines():
    assert branch_git.open_pr_heads("story/a\n\n story/b \n") == {"story/a", "story/b"}


def test_a_branch_landed_when_its_merge_reached_main_not_when_main_last_moved(clone):
    push_branch(clone, "story/merged", ["a.txt"])
    commit(clone, "other.txt")  # main moves on after the branch was cut
    git(clone, "merge", "-q", "--no-ff", "-m", "merge", "story/merged", date="2026-01-03T10:00:00+00:00")
    commit(clone, "later.txt")
    git(clone, "push", "-q", "origin", "main")
    git(clone, "fetch", "-q", "origin")

    landed = {b.name: b for b in branch_git.read_branches()}["story/merged"].landed_at

    assert landed.isoformat() == "2026-01-03T10:00:00+00:00"
