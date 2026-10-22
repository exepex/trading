"""22 Oct 2026's stop ("couldn't find remote ref claude/..."): the owner's scheduled session checks out its own
session branch, which origin has never seen. Every fetch, compare, pull and push of the run targets main, whatever
branch the checkout is on."""

from datetime import date

from fno.books.decided_runs import GitDecidedRuns
from fno.constants import BOOK1_RULES, PUBLISH_BRANCH
from fno.desk.git_sync import Git, GitCommitter
from fno.playbook.history import PlaybookGit

from .test_git_sync import checkouts, git  # noqa: F401 - the fixture: two checkouts of one origin

SESSION = "claude/bold-thompson-2lkkg6"


def on_session_branch(clone) -> None:
    git(clone, "checkout", "-q", "-b", SESSION)  # never pushed: origin has no such ref


def test_a_checkout_on_an_unpublished_session_branch_commits_and_pushes_to_main(checkouts):  # noqa: F811
    a, b = checkouts
    on_session_branch(a)
    (a / "run.json").write_text("{}")
    commit = GitCommitter(Git(a)).commit([a / "run.json"], "Desk run step quotes")
    assert git(b, "ls-remote", "origin", "main").split()[0] == commit
    assert git(b, "ls-remote", "origin", SESSION) == ""  # nothing published under the session's name
    assert Git(a).unpushed() == [] and Git(a).unpushed_files() == []


def test_a_session_branch_pulls_main_before_it_commits(checkouts):  # noqa: F811
    a, b = checkouts
    (b / "other.txt").write_text("from main\n")
    git(b, "add", "other.txt")
    git(b, "commit", "-q", "-m", "another writer")
    git(b, "push", "-q", "origin", "main")
    on_session_branch(a)
    (a / "run.json").write_text("{}")
    other = git(b, "rev-parse", "HEAD").strip()
    commit = GitCommitter(Git(a)).commit([a / "run.json"], "Desk run step quotes")
    parents = git(a, "rev-list", "--parents", "-n", "1", commit).split()[1:]
    assert parents == [other]  # built on main's newest commit: no rejected push and no retry's merge (judge 474)
    git(b, "pull", "-q", "origin", "main")
    assert (b / "run.json").is_file() and (a / "other.txt").is_file()


def test_the_decided_runs_and_the_playbook_read_main_from_a_session_branch(checkouts):  # noqa: F811
    a, b = checkouts
    on_session_branch(a)
    assert GitDecidedRuns(Git(a), BOOK1_RULES).find(date(2026, 10, 22)) == []  # no "couldn't find remote ref"
    (b / "new.txt").write_text("x\n")
    git(b, "add", "new.txt")
    git(b, "commit", "-q", "-m", "on main")
    git(b, "push", "-q", "origin", "main")
    assert PlaybookGit(a).observed() == git(b, "rev-parse", "HEAD").strip()


def test_the_target_is_main():
    assert PUBLISH_BRANCH == "main" and Git(".").target == "main"
