"""Story O1, gap G4 (judge 419): the run's one committer accepts its own commits that it could not push yet, checked by
content, also after a rerun reads them back from the git-ignored list; a stranger's commit is still refused, and the
list is emptied once a push carries them."""

import json
import subprocess
from pathlib import Path

import pytest

from fno.desk.daily_ports import CommitFailed
from fno.desk.git_sync import Git, GitCommitter
from fno.desk.own_commits import OWN_UNPUSHED_FILE, OwnUnpushed

REPOSITORY = Path(__file__).resolve().parents[2]
REJECT_WHILE_FLAGGED = """#!/bin/sh
test -f "{flag}" && exit 1
exit 0
"""


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


@pytest.fixture
def root(tmp_path):
    """A committed checkout pushing to a bare origin whose pushes are rejected while `root/../reject` exists."""
    root, origin = tmp_path / "checkout", tmp_path / "origin.git"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    for key, value in (("user.email", "t@example.org"), ("user.name", "t"), ("core.hooksPath", "/dev/null")):
        git(root, "config", key, value)
    (root / "start.txt").write_text("start\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "start")
    subprocess.run(["git", "clone", "-q", "--bare", str(root), str(origin)], check=True, capture_output=True)
    git(root, "remote", "add", "origin", str(origin))
    git(root, "fetch", "-q", "origin")
    hook = origin / "hooks" / "pre-receive"
    hook.write_text(REJECT_WHILE_FLAGGED.format(flag=tmp_path / "reject"), encoding="utf-8")
    hook.chmod(0o755)
    return root


def reject(root, on: bool) -> None:
    flag = root.parent / "reject"
    flag.touch() if on else flag.unlink()


def write(root, name, text) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def committer(root) -> GitCommitter:
    return GitCommitter(Git(root), OwnUnpushed(root / OWN_UNPUSHED_FILE))


def origin_subjects(root) -> list[str]:
    return git(root, "log", "--format=%s", "origin/main").split()


def unpushed_part(root, run: GitCommitter) -> None:
    reject(root, True)
    with pytest.raises(CommitFailed) as failed:
        run.commit([write(root, "quotes/nifty.json", "nifty\n")], "part-nifty")
    assert failed.value.unpushed
    reject(root, False)


def test_a_part_s_unpushed_commit_is_carried_by_the_next_commit_and_the_list_is_emptied(root):
    run = committer(root)
    unpushed_part(root, run)
    assert [c.message for c in run.own.commits] == ["part-nifty"]
    run.commit([write(root, "journal/pack.json", "pack\n")], "step-pack")
    assert origin_subjects(root)[:2] == ["step-pack", "part-nifty"]
    assert run.own.commits == [] and json.loads((root / OWN_UNPUSHED_FILE).read_text(encoding="utf-8")) == []


def test_a_stranger_s_unpushed_commit_is_still_refused_beside_the_run_s_own(root):
    run = committer(root)
    unpushed_part(root, run)
    git(root, "add", "-f", "--", write(root, "other.txt", "stranger\n"))
    git(root, "commit", "-q", "-m", "a-commit-the-run-did-not-make")
    with pytest.raises(CommitFailed, match="a-commit-the-run-did-not-make"):
        run.commit([write(root, "journal/pack.json", "pack\n")], "step-pack")
    assert "part-nifty" not in origin_subjects(root)


def test_a_rerun_accepts_its_own_commit_from_the_list_by_content(root):
    unpushed_part(root, committer(root))
    committer(root).commit([write(root, "journal/pack.json", "pack\n")], "step-pack")  # a new committer: the rerun
    assert "part-nifty" in origin_subjects(root)


def test_a_rerun_refuses_its_own_commit_once_its_files_changed(root):
    unpushed_part(root, committer(root))
    git(root, "add", "--", write(root, "quotes/nifty.json", "edited\n"))
    git(root, "commit", "-q", "--amend", "--no-edit")  # same message, other content
    with pytest.raises(CommitFailed, match="part-nifty"):
        committer(root).commit([write(root, "journal/pack.json", "pack\n")], "step-pack")


def test_the_list_is_git_ignored_so_it_is_never_committed():
    for name in (OWN_UNPUSHED_FILE, f"{OWN_UNPUSHED_FILE}.tmp"):
        checked = subprocess.run(["git", "-C", str(REPOSITORY), "check-ignore", "-q", name], check=False)
        assert checked.returncode == 0, name
