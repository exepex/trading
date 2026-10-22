"""The counting rule on real git history, the research engine's `Git` and D6's real `Versions` (story MS-P1h): ancestry
decides, not dates. Includes judge 480's plants: the first counted session moved after the decisions, and a later
card version."""

import subprocess
from datetime import date
from pathlib import Path

import pytest

from fno.books.version_registry import VersionRow, render
from fno.books.versions import Versions
from fno.research_engine.ledger import Git
from fno.school.registration.counting import CARD_PATH, CONFIG_PATH, CountingRule, NotCounted
from fno.school.registration.wiring import CARD_COMPONENT, D6VersionLookup, GitCountingHistory
from tests.school.registration.fakes import CARD_SHA, SESSION, candidate

FIRST = "2026-11-30"


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return done.stdout.strip()


def commit(repo: Path, name: str, text: str) -> str:
    (repo / name).parent.mkdir(parents=True, exist_ok=True)
    (repo / name).write_text(text)
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", f"{name}: {text}")
    return git(repo, "rev-parse", "HEAD")


def config(first: str | None) -> str:
    return f"school:\n  enabled: false\n  first_counted: {first or ''}\n"


class Repo:
    """A repository with the registered pieces committed in order; `decide` commits a sealed decision."""

    def __init__(self, path: Path):
        git(path, "init", "-q", "-b", "main")
        for setting in (("user.name", "t"), ("user.email", "t@example.invalid"), ("commit.gpgsign", "false")):
            git(path, "config", *setting)
        self.path, self.git = path, Git(path)
        self.components = commit(path, "research/school/cards/CS1.md", "cs1 v1")
        self.row = VersionRow("school:CS1@1", "1", date(2026, 11, 1), self.components, {CARD_COMPONENT: CARD_SHA}, "p")

    def register(self, first: str | None = FIRST) -> None:
        commit(self.path, "journal/versions.csv", render([self.row]))
        commit(self.path, CARD_PATH, "the frozen comparison card")
        commit(self.path, CONFIG_PATH, config(first))

    def decide(self, name: str = "decision") -> str:
        return commit(self.path, f"receipts/{name}.txt", "sealed")

    def verdict(self, decision: str, **changes):
        history = GitCountingHistory(self.git)
        rule = CountingRule(history, D6VersionLookup(Versions([self.row], self.git)))
        return rule.verdict(candidate(commit=decision, **changes))


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path)


def test_the_rule_counts_by_ancestry_on_real_history(repo):
    repo.register()
    assert repo.verdict(repo.decide()).counted


def test_a_first_counted_session_moved_back_after_the_decision_never_re_counts_it(repo):
    repo.register("2026-12-15")
    decision = repo.decide()  # the session 30 Nov is before the first counted session in force: not counted
    commit(repo.path, CONFIG_PATH, config(FIRST))  # the date is moved back afterwards: judge 480's plant
    assert repo.verdict(decision).reason == NotCounted.BEFORE_FIRST_COUNTED_SESSION


def test_a_first_counted_session_moved_later_after_the_decision_never_un_counts_it(repo):
    repo.register(FIRST)
    decision = repo.decide()
    commit(repo.path, CONFIG_PATH, config("2026-12-15"))
    assert repo.verdict(decision).counted


def test_a_first_counted_session_set_after_the_decision_does_not_count_it(repo):
    commit(repo.path, "journal/versions.csv", render([repo.row]))
    commit(repo.path, CARD_PATH, "the frozen comparison card")
    decision = repo.decide()
    commit(repo.path, CONFIG_PATH, config(FIRST))
    assert repo.verdict(decision).reason == NotCounted.NO_FIRST_COUNTED_SESSION


def test_a_first_counted_session_written_in_the_decisions_own_commit_is_refused(repo):
    commit(repo.path, "journal/versions.csv", render([repo.row]))
    commit(repo.path, CARD_PATH, "the frozen comparison card")
    decision = commit(repo.path, CONFIG_PATH, config(FIRST))
    assert repo.verdict(decision).reason == NotCounted.FIRST_COUNTED_NOT_FROZEN_BEFORE


def test_a_card_edited_after_the_decision_leaves_it_counted_under_the_version_in_force(repo):
    repo.register()
    decision = repo.decide()
    version_1 = repo.git.commits_touching(CARD_PATH)[-1]
    version_2 = commit(repo.path, CARD_PATH, "the card, new version")
    later = repo.decide("later")
    assert repo.verdict(decision).card_commit == version_1
    assert repo.verdict(later).card_commit == version_2 and repo.verdict(later).counted


def test_a_card_committed_after_the_decision_makes_it_not_counted(repo):
    commit(repo.path, "journal/versions.csv", render([repo.row]))
    commit(repo.path, CONFIG_PATH, config(FIRST))
    decision = repo.decide()
    commit(repo.path, CARD_PATH, "the frozen comparison card")
    assert repo.verdict(decision).reason == NotCounted.CARD_NOT_FROZEN_BEFORE


def test_a_version_row_committed_after_the_decision_is_not_counted(repo):
    commit(repo.path, CARD_PATH, "the frozen comparison card")
    commit(repo.path, CONFIG_PATH, config(FIRST))
    decision = repo.decide()
    commit(repo.path, "journal/versions.csv", render([repo.row]))
    assert repo.verdict(decision).reason == NotCounted.VERSION_NOT_REGISTERED_BEFORE


def test_a_changed_driver_card_sha_is_refused_on_real_history(repo):
    repo.register()
    assert repo.verdict(repo.decide(), card_sha256="cd" * 32).reason == NotCounted.DRIVER_CARD_CHANGED


def test_a_session_before_the_first_counted_session_is_not_counted(repo):
    repo.register()
    assert repo.verdict(repo.decide(), session=date(2026, 11, 27)).reason == NotCounted.BEFORE_FIRST_COUNTED_SESSION


def test_the_history_reads_the_value_in_each_commits_tree(repo):
    first = commit(repo.path, CONFIG_PATH, config(FIRST))
    moved = commit(repo.path, CONFIG_PATH, config("2026-12-15"))
    history = GitCountingHistory(repo.git)
    assert (history.first_counted_at(first).day, history.first_counted_at(first).set_in) == (date(2026, 11, 30), first)
    assert (history.first_counted_at(moved).day, history.first_counted_at(moved).set_in) == (date(2026, 12, 15), moved)
    assert history.first_counted_at(repo.components).day is None, "a tree without the setting has none"


def test_the_card_commit_list_and_ancestry_come_from_the_engines_git(repo):
    one = commit(repo.path, CARD_PATH, "1")
    two = commit(repo.path, CARD_PATH, "2")
    history = GitCountingHistory(repo.git)
    assert history.card_commits() == [one, two] and history.is_ancestor(one, two) and not history.is_ancestor(two, one)
    assert date(2026, 11, 30) == SESSION
