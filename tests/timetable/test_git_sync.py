"""Story E3 with E1's across-containers rule, on real git repositories: two desk checkouts of one origin. A push
rejected because the other container pushed first drops the local account commit, resets to the new origin and applies
the same fills again; nothing is lost and nothing is written twice. The committer pulls before it pushes."""

import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest

from fno.books.paths import book_folder
from fno.constants import BOOK1_RULES, BOOK2_HYBRID
from fno.desk.git_sync import CheckoutNotDedicated, Git, GitAccountSync, GitCommitter


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


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "sent"


def sync_for(clone: Path, alerts=None) -> GitAccountSync:
    @contextmanager
    def open_journal(book):
        yield Journal(book_folder(clone, book) / "account")

    return GitAccountSync(Git(clone), open_journal, alerts or Alerts())


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


@pytest.mark.parametrize("other", ["unpushed commit", "tracked edit"])
def test_an_account_write_is_refused_in_a_checkout_holding_other_work(checkouts, other):
    """Judge 82's probe: an unpushed decision commit or an uncommitted tracked edit must never be reset over."""
    _, b = checkouts
    if other == "unpushed commit":
        (b / "decision.json").write_text("{}")
        git(b, "add", "decision.json")
        git(b, "commit", "-q", "-m", "a decision run, not pushed yet")
    else:
        (b / "README").write_text("edited, not committed\n")
    alerts, applied = Alerts(), []
    with pytest.raises(CheckoutNotDedicated, match="holds other work"):
        sync_for(b, alerts).write(BOOK2_HYBRID, lambda j: applied.append(j), "fills b1")
    assert applied == [] and len(alerts.sent) == 1
    kept = (b / "decision.json").is_file() if other == "unpushed commit" else "edited" in (b / "README").read_text()
    assert kept


def test_a_rejected_push_is_not_reset_when_more_than_this_write_is_ahead(checkouts):
    """Other work committed during the write (here by the apply itself) would be lost by a reset: stop and alert."""
    a, b = checkouts
    alerts = Alerts()

    def fill_and_commit_more(journal):
        git(a, "commit", "-q", "--allow-empty", "-m", "another container")
        git(a, "push", "-q", "origin", "main")
        (b / "other.json").write_text("{}")
        git(b, "add", "other.json")
        git(b, "commit", "-q", "-m", "other work in this checkout")
        journal.fill("b1-open")

    with pytest.raises(CheckoutNotDedicated, match="2 commit\\(s\\) ahead"):
        sync_for(b, alerts).write(BOOK2_HYBRID, fill_and_commit_more, "fills b1")
    assert (b / "other.json").is_file() and "NOT reset" in alerts.sent[0]
