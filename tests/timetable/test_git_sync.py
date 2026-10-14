"""Story E3 with E1's across-containers rule, on real git repositories: two desk checkouts of one origin. A push
rejected because the other container pushed first drops the local account commit, resets to the new origin and applies
the same fills again; nothing is lost and nothing is written twice. The committer pulls before it pushes."""

import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest

from fno.books.paths import book_folder
from fno.constants import BOOK1_RULES, BOOK2_HYBRID
from fno.desk.git_sync import Git, GitAccountSync, GitCommitter


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


class Journal:
    """Stands in for a book's journal: a fill is one file named by its fill ID (idempotent, like E1's)."""

    def __init__(self, folder: Path):
        self.folder = folder

    def fill(self, fill_id: str) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        (self.folder / f"{fill_id}.txt").write_text(fill_id)


def sync_for(clone: Path) -> GitAccountSync:
    @contextmanager
    def open_journal(book):
        yield Journal(book_folder(clone, book) / "account")

    return GitAccountSync(Git(clone), open_journal)


def test_a_rejected_push_resets_and_applies_the_same_fills_again(checkouts):
    a, b = checkouts
    sync_for(a).write(BOOK1_RULES, lambda j: j.fill("t1-open"), "fills t1")  # container A pushes first
    applied = []

    def fill_b(journal):
        applied.append(1)
        if len(applied) == 1:  # B's checkout is behind: its first push will be rejected
            git(a, "commit", "-q", "--allow-empty", "-m", "another container")
            git(a, "push", "-q", "origin", "main")
        journal.fill("b1-open")

    sync_for(b).write(BOOK2_HYBRID, fill_b, "fills b1")
    git(a, "pull", "-q", "origin", "main")
    names = sorted(p.name for p in (a / "journal").rglob("*.txt"))
    assert names == ["b1-open.txt", "t1-open.txt"] and len(applied) == 2
    assert git(a, "log", "--format=%s").splitlines().count("fills b1") == 1  # the rejected commit was dropped


def test_the_committer_pulls_commits_and_pushes(checkouts):
    a, b = checkouts
    (a / "journal").mkdir()
    (a / "journal" / "run.json").write_text("{}")
    commit = GitCommitter(Git(a)).commit([a / "journal" / "run.json"], "Desk run step")
    git(b, "pull", "-q", "origin", "main")
    assert (b / "journal" / "run.json").is_file() and git(b, "rev-parse", "HEAD").strip() == commit
    assert GitCommitter(Git(a)).commit([a / "journal" / "run.json"], "nothing new") == commit  # nothing to commit
