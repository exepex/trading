"""Story GB1: what git and GitHub say about the remote branches, and the one call that deletes one. Everything that
touches the outside is here, so `branch_rules.py` stays pure and the tests inject fakes for the two network calls."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

from branch_rules import DEFAULT_BRANCH, Branch

ROOT = Path(__file__).resolve().parent.parent
REMOTE = "origin"
MAIN_REF = f"{REMOTE}/{DEFAULT_BRANCH}"
REGISTER = ROOT / "docs" / "WORK_REGISTER.md"
KEEP_LIST = ROOT / ".github" / "branch-keep.txt"


def git(*args: str) -> str:
    done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if done.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {done.stderr.strip()[-300:]}")
    return done.stdout.strip()


def _time(text: str) -> datetime:
    return datetime.fromisoformat(text).astimezone(UTC)


def _main_line() -> list[str]:
    """Main's own line (first parents), oldest first."""
    return git("rev-list", "--first-parent", "--reverse", MAIN_REF).split()


def _is_ancestor(sha: str, of: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", sha, of], cwd=ROOT).returncode == 0


def _landed_at(sha: str, main_line: list[str]) -> datetime | None:
    """The oldest commit on main's own line that holds the tip: when the branch reached main, however many merges deep
    (a branch merged into another branch that was merged later reaches main only with the last one). Once a main-line
    commit holds the tip every later one does, so a binary search finds it."""
    low, high = 0, len(main_line)
    while low < high:
        middle = (low + high) // 2
        if _is_ancestor(sha, main_line[middle]):
            high = middle
        else:
            low = middle + 1
    return _time(git("show", "-s", "--format=%cI", main_line[low])) if low < len(main_line) else None


# a branch that alone changes these holds unfinished work
WORK_PATHS = ("fno", "tools", "tests", ".github", "config.yaml", "research/data", "receipts", "journal")


def unique_work_files(sha: str) -> int:
    """Code files touched by commits only on the branch (a patch-equal copy on main does not count)."""
    unique = [line[2:] for line in git("cherry", MAIN_REF, sha).splitlines() if line.startswith("+ ")]
    touched = {
        f
        for commit in unique
        for f in git("diff-tree", "--no-commit-id", "--name-only", "-r", commit, "--", *WORK_PATHS).split()
    }
    return len(touched)


def read_branches(with_code: bool = False) -> list[Branch]:
    main_line = _main_line()
    merged = set(git("branch", "-r", "--merged", MAIN_REF, "--format=%(refname:lstrip=3)").split())
    fields = "%(refname:lstrip=3)|%(objectname)|%(committerdate:iso-strict)"
    found = []
    for line in git("for-each-ref", f"refs/remotes/{REMOTE}", f"--format={fields}").splitlines():
        name, sha, date = line.rsplit("|", 2)
        if name == "HEAD":
            continue
        is_merged = name in merged
        ahead = 0 if is_merged else int(git("rev-list", "--count", f"{MAIN_REF}..{sha}"))
        landed = _landed_at(sha, main_line) if is_merged else None
        code = unique_work_files(sha) if with_code and ahead else 0
        found.append(Branch(name, sha, _time(date), is_merged, ahead, landed, code))
    return found


def remote_heads() -> dict[str, str]:
    """Every branch's head on GitHub right now (one call, not the fetched copies)."""
    heads = {}
    for line in git("ls-remote", "--heads", REMOTE).splitlines():
        sha, ref = line.split()
        heads[ref.removeprefix("refs/heads/")] = sha
    return heads


def open_pr_heads(gh_list: str) -> frozenset[str]:
    """Head branches of open pull requests, one name per line (`gh pr list --json headRefName -q '.[].headRefName'`)."""
    return frozenset(line.strip() for line in gh_list.splitlines() if line.strip())


def delete_remote_branch(name: str, sha: str) -> None:
    """Delete only if GitHub still holds `sha` for the branch: a push since the check makes git refuse."""
    ref = f"refs/heads/{name}"
    done = subprocess.run(
        ["git", "push", REMOTE, f"--force-with-lease={ref}:{sha}", f":{ref}"], cwd=ROOT, capture_output=True, text=True
    )
    if done.returncode:
        raise RuntimeError(f"delete {name}: {(done.stderr or done.stdout).strip()[-300:]}")
