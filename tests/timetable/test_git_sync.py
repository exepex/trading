"""Story E3 on real git repositories: two desk checkouts of one origin. The committer pulls before it pushes (since
story E2c the accounts live in Drive, so only the run's public files are committed)."""

import subprocess
from pathlib import Path

import pytest

from fno.desk.git_sync import Git, GitCommitter


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def checkouts(tmp_path):
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    clones = []
    for name in ("a", "b"):
        clone = tmp_path / name
        git(tmp_path, "clone", "-q", str(origin), str(clone))
        git(clone, "config", "user.email", "desk@example.invalid")
        git(clone, "config", "user.name", "desk")
        git(clone, "checkout", "-q", "-b", "main")
        clones.append(clone)
    (clones[0] / "README").write_text("desk\n")
    git(clones[0], "add", "README")
    git(clones[0], "commit", "-q", "-m", "start")
    git(clones[0], "push", "-q", "origin", "main")
    git(clones[1], "pull", "-q", "origin", "main")
    return clones


def test_the_committer_pulls_commits_and_pushes(checkouts):
    a, b = checkouts
    (a / "journal").mkdir()
    (a / "journal" / "run.json").write_text("{}")
    commit = GitCommitter(Git(a)).commit([a / "journal" / "run.json"], "Desk run step")
    git(b, "pull", "-q", "origin", "main")
    assert (b / "journal" / "run.json").is_file() and git(b, "rev-parse", "HEAD").strip() == commit
    assert GitCommitter(Git(a)).commit([a / "journal" / "run.json"], "nothing new") == commit  # nothing to commit
