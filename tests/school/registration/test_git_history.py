"""The counting rule on real git history and D6's real `Versions` (story MS-P1h): ancestry decides, not dates."""

import subprocess
from datetime import date
from pathlib import Path

from fno.books.version_registry import VersionRow, render
from fno.books.versions import Versions
from fno.school.registration.counting import CARD_PATH, CountingRule, NotCounted
from fno.school.registration.wiring import CARD_COMPONENT, D6VersionLookup, GitCardHistory
from tests.school.registration.fakes import CARD_SHA, SESSION, candidate


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return done.stdout.strip()


def commit(repo: Path, name: str, text: str) -> str:
    (repo / name).parent.mkdir(parents=True, exist_ok=True)
    (repo / name).write_text(text)
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", f"{name}: {text}")
    return git(repo, "rev-parse", "HEAD")


def repository(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    for setting in (("user.name", "t"), ("user.email", "t@example.invalid"), ("commit.gpgsign", "false")):
        git(tmp_path, "config", *setting)
    return tmp_path


class RegistryHistory(GitCardHistory):
    """D6's `GitHistory` over the same repository: the registry row's own commit comes from git's text search."""

    def first_commit_containing(self, text: str, path: str) -> str | None:
        found = git(self.repository, "log", "--format=%H", "-S", text, "--", path).splitlines()
        return found[-1] if found else None


def test_the_rule_counts_by_ancestry_on_real_history(tmp_path):
    repo = repository(tmp_path)
    components = commit(repo, "research/school/cards/CS1.md", "cs1 v1")
    history = RegistryHistory(repo)
    row = VersionRow("school:CS1@1", "1", date(2026, 11, 1), components, {CARD_COMPONENT: CARD_SHA}, "pilot")
    commit(repo, "journal/versions.csv", render([row]))
    commit(repo, CARD_PATH, "the frozen comparison card")
    decision = commit(repo, "receipts/decision.txt", "sealed")
    rule = CountingRule(SESSION, history, D6VersionLookup(Versions([row], history)))
    assert rule.verdict(candidate(commit=decision)).counted


def test_a_card_edited_after_the_decision_makes_the_decision_not_counted(tmp_path):
    repo = repository(tmp_path)
    components = commit(repo, "research/school/cards/CS1.md", "cs1 v1")
    row = VersionRow("school:CS1@1", "1", date(2026, 11, 1), components, {CARD_COMPONENT: CARD_SHA}, "pilot")
    commit(repo, "journal/versions.csv", render([row]))
    commit(repo, CARD_PATH, "the frozen comparison card")
    decision = commit(repo, "receipts/decision.txt", "sealed")
    commit(repo, CARD_PATH, "the card edited later")
    history = RegistryHistory(repo)
    verdict = CountingRule(SESSION, history, D6VersionLookup(Versions([row], history))).verdict(
        candidate(commit=decision)
    )
    assert (verdict.counted, verdict.reason) == (False, NotCounted.CARD_NOT_FROZEN_BEFORE)


def test_a_version_row_committed_after_the_decision_is_not_counted(tmp_path):
    repo = repository(tmp_path)
    components = commit(repo, "research/school/cards/CS1.md", "cs1 v1")
    row = VersionRow("school:CS1@1", "1", date(2026, 11, 1), components, {CARD_COMPONENT: CARD_SHA}, "pilot")
    commit(repo, CARD_PATH, "the frozen comparison card")
    decision = commit(repo, "receipts/decision.txt", "sealed")
    commit(repo, "journal/versions.csv", render([row]))  # registered after the decision
    history = RegistryHistory(repo)
    verdict = CountingRule(SESSION, history, D6VersionLookup(Versions([row], history))).verdict(
        candidate(commit=decision)
    )
    assert verdict.reason == NotCounted.VERSION_NOT_REGISTERED_BEFORE


def test_the_git_history_names_the_last_commit_of_a_file_and_none_for_an_unknown_one(tmp_path):
    repo = repository(tmp_path)
    first = commit(repo, "a.txt", "1")
    second = commit(repo, "a.txt", "2")
    history = GitCardHistory(repo)
    assert history.last_commit("a.txt") == second and history.last_commit("missing.txt") is None
    assert history.is_ancestor(first, second) and not history.is_ancestor(second, first)
