"""A failed git command is an error, never an empty answer (orchestrator, 22 Oct 2026: a silent failure turned a real,
published AI reveal into a permanent miss). Each method family keeps git's real answers, "not there" included, and
raises `GitFailed` on any other failure."""

import subprocess
from datetime import date

import pytest

from fno.playbook.history import PlaybookGit
from fno.research_engine.ledger import Git, GitFailed

REAL = subprocess.run
BROKEN = "fatal: unable to read tree (simulated: out of memory)"


def repo(tmp_path):
    def git(*args):
        return REAL(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True).stdout.strip()

    git("init", "-q", "-b", "main")
    git("config", "user.email", "desk@example.invalid")
    git("config", "user.name", "desk")
    (tmp_path / "a.txt").write_text("one\n")
    git("add", "a.txt")
    git("commit", "-qm", "one")
    first = git("rev-parse", "HEAD")
    (tmp_path / "b.txt").write_text("two\n")
    git("add", "b.txt")
    git("commit", "-qm", "two")
    return first, git("rev-parse", "HEAD")


@pytest.fixture
def failing(monkeypatch):
    """Every git call with this subcommand fails as a broken repository would (exit 128, not a 'not there' answer)."""

    def install(subcommand):
        def run(args, *a, **k):
            if args[:2] == ["git", subcommand]:
                return subprocess.CompletedProcess(args, 128, "", BROKEN)
            return REAL(args, *a, **k)

        monkeypatch.setattr(subprocess, "run", run)

    return install


def test_output_reads_answer_or_raise(tmp_path, failing):
    first, head = repo(tmp_path)
    git = Git(tmp_path)
    assert git.head() == head and git.commits_touching("a.txt") == [first]
    assert git.commits_touching("never.txt") == [] and git.first_commit_containing("nothing", "a.txt") is None
    failing("log")
    for read in (lambda: git.commits_touching("a.txt"), lambda: git.first_commit_containing("one", "a.txt")):
        with pytest.raises(GitFailed, match="git log failed \\(exit 128\\): fatal: unable to read tree"):
            read()


def test_a_history_with_no_commits_yet_is_empty_and_no_repository_at_all_raises(tmp_path):
    (tmp_path / "empty").mkdir()
    REAL(["git", "init", "-q", str(tmp_path / "empty")], check=True)
    assert Git(tmp_path / "empty").commits_touching("a.txt") == []  # git's own "no commits yet": a true answer
    (tmp_path / "plain").mkdir()
    with pytest.raises(GitFailed, match="not a git repository"):
        Git(tmp_path / "plain").commits_touching("a.txt")


def test_committed_text_is_none_only_when_git_says_it_is_not_there(tmp_path, failing):
    first, head = repo(tmp_path)
    git = PlaybookGit(tmp_path)
    assert git.committed_text("a.txt") == "one\n" and git.committed_bytes("a.txt", head) == b"one\n"
    assert git.committed_text("b.txt", first) is None and git.committed_text("never.txt") is None
    assert git.committed_text("a.txt", "0" * 40) is None  # git: "exists on disk, but not in" that revision
    with pytest.raises(GitFailed, match="invalid object name"):  # a revision git cannot resolve: a wrong question
        git.committed_text("a.txt", "HEAD~9")
    failing("show")
    with pytest.raises(GitFailed):
        git.committed_text("a.txt")
    with pytest.raises(GitFailed):
        git.committed_bytes("a.txt", head)


def test_exit_code_answers_keep_their_meaning(tmp_path):
    first, head = repo(tmp_path)
    git = Git(tmp_path)
    assert git.is_ancestor(first, head) and not git.is_ancestor(head, first) and not git.is_ancestor("0" * 40, head)
    assert git.commit_exists(head) and not git.commit_exists("0" * 40)
    assert git.unchanged_since(head, "a.txt") and not git.unchanged_since(first, "b.txt")


@pytest.mark.parametrize(
    ("subcommand", "question"),
    [("merge-base", lambda git, first, head: git.is_ancestor(first, head)),
     ("cat-file", lambda git, first, head: git.commit_exists(head)),
     ("diff", lambda git, first, head: git.unchanged_since(head, "a.txt"))],
)  # fmt: skip
def test_an_exit_code_answer_raises_on_a_failure(tmp_path, failing, subcommand, question):
    first, head = repo(tmp_path)
    failing(subcommand)
    with pytest.raises(GitFailed):
        question(Git(tmp_path), first, head)


def test_a_refused_pull_raises_instead_of_showing_a_stale_checkout_as_current(tmp_path):
    repo(tmp_path)  # no remote: the pull is refused
    with pytest.raises(GitFailed, match="git pull failed"):
        PlaybookGit(tmp_path).observed()


def test_g13bs_deep_enough_raises_when_the_shallow_check_or_the_fetch_fails(tmp_path, failing):
    """price_ranges/wiring.py's `deep_enough` (G13b) now goes through B4's Git: a failed shallow check or a refused
    fetch raises, never "not shallow" or a fetch that silently did not happen."""
    from fno.price_ranges.wiring import deep_enough

    repo(tmp_path)
    deep_enough(tmp_path)  # a full clone: nothing to fetch
    failing("rev-parse")
    with pytest.raises(GitFailed, match="git rev-parse failed"):
        deep_enough(tmp_path)


def test_a_refused_shallow_fetch_raises(tmp_path):
    repo(tmp_path)  # no remote "origin": the fetch is refused
    with pytest.raises(GitFailed, match="git fetch failed"):
        Git(tmp_path).deepen_since(date(2026, 10, 12), "main")


def test_the_playbooks_added_reads_answer_or_raise(tmp_path, failing):
    """`added_at` and `added_in` (the fills read each recorded run's commit back with `added_in`)."""
    first, _ = repo(tmp_path)
    git = PlaybookGit(tmp_path)
    assert git.added_in("a.txt")[0] == first and git.added_at("a.txt") == git.added_in("a.txt")[1]
    assert git.added_in("never.txt") is None and git.added_at("never.txt") is None
    failing("log")
    for read in (lambda: git.added_in("a.txt"), lambda: git.added_at("a.txt")):
        with pytest.raises(GitFailed, match="git log failed"):
            read()


def test_tree_matches_raises_when_its_diff_fails(tmp_path, failing):
    _, head = repo(tmp_path)
    git = PlaybookGit(tmp_path)
    assert git.tree_matches(head, ("a.txt",))
    (tmp_path / "a.txt").write_text("changed\n")
    assert not git.tree_matches(head, ("a.txt",))
    failing("diff")
    with pytest.raises(GitFailed, match="git diff failed"):
        git.tree_matches(head, ("a.txt",))


def test_the_health_checks_pickaxe_answers_or_raises(tmp_path, failing):
    from fno.health.evidence import HealthHistory

    first, _ = repo(tmp_path)
    history = HealthHistory(tmp_path)
    assert history.first_commit_adding_text("a.txt", "one", date(2000, 1, 1)) == first
    assert history.first_commit_adding_text("a.txt", "never written", date(2000, 1, 1)) is None
    failing("log")
    with pytest.raises(GitFailed, match="git log failed"):
        history.first_commit_adding_text("a.txt", "one", date(2000, 1, 1))


def test_the_factorys_staged_paths_answer_or_raise(tmp_path, failing):
    from fno.factory.staging import FactoryGit

    repo(tmp_path)
    git = FactoryGit(tmp_path)
    assert git.staged_paths() == []
    (tmp_path / "c.txt").write_text("three\n")
    REAL(["git", "add", "c.txt"], cwd=tmp_path, check=True)
    assert git.staged_paths() == ["c.txt"]
    failing("diff")
    with pytest.raises(GitFailed, match="git diff failed"):
        git.staged_paths()


def test_git_answers_in_english_whatever_the_locale(tmp_path, monkeypatch):
    """The "not there" answers are matched by git's English text, so every call pins the C locale."""
    seen = []
    monkeypatch.setenv("LC_ALL", "de_DE.UTF-8")
    monkeypatch.setattr(subprocess, "run", lambda args, *a, **k: seen.append(k["env"]) or REAL(args, *a, **k))
    repo(tmp_path)
    seen.clear()
    assert PlaybookGit(tmp_path).committed_text("never.txt") is None
    assert seen and all(env["LC_ALL"] == "C" for env in seen)
