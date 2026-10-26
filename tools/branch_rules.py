"""Story GB1: which remote branches may go. Pure rules, no git and no network (`branch_git.py` reads,
`branch_cleanup.py` acts). A branch is deleted only when nothing says it is in use; every doubt keeps it
(docs/stories/GB1-branch-cleanup.md)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

DEFAULT_BRANCH = "main"
GRACE = timedelta(hours=24)  # a merged branch stays this long after it landed on main (a builder may still push)
RECENT = timedelta(hours=48)  # an unmerged branch with a newer commit is treated as being worked on
REHEARSAL_PREFIX = "rehearsal/"
REHEARSAL_WHY = "rehearsal run: REH1 Q3 (owner, 24 Oct) keeps them for inspection until the owner says otherwise"
BRANCH_TOKEN = re.compile(r"[A-Za-z0-9_./-]+")  # a branch name, with or without a slash; a loose match only keeps more

KEEP, KEEP_UNSURE, DELETE = "keep", "keep-unsure", "delete"


@dataclass(frozen=True)
class Branch:
    name: str
    sha: str
    tip_time: datetime  # the tip commit's committer time, UTC
    merged: bool  # the tip is an ancestor of origin/main
    ahead: int  # commits on the branch that are not on origin/main
    landed_at: datetime | None = None  # the main commit that first held the tip; None when not merged
    work_files: int = 0  # code files only this branch changes (inventory only; 0 = nothing of value would be lost)


@dataclass(frozen=True)
class Evidence:
    """Everything outside the branch itself that says it is in use."""

    keep_list: dict[str, str]  # name -> why, from .github/branch-keep.txt
    register: frozenset[str]  # names in docs/WORK_REGISTER.md's Branch column
    open_prs: frozenset[str]  # head branches of open pull requests
    recent_mentions: frozenset[str] = frozenset()  # names in files written in the last 48 h (inventory only)


def parse_keep_list(text: str) -> dict[str, str]:
    kept = {}
    for line in text.splitlines():
        name, _, why = re.sub(r"^\s*#.*", "", line).partition(" #")  # a comment starts at "#" after a space
        if name.strip():
            kept[name.strip()] = why.strip() or "keep list"
    return kept


def names_in(text: str) -> set[str]:
    return {
        t for t in (token.rstrip(".") for token in BRANCH_TOKEN.findall(text)) if re.search("[A-Za-z0-9]", t)
    }  # a sentence's full stop is not part of a name


def register_branches(text: str) -> frozenset[str]:
    """Branch names in the Branch column (the 4th) of the register's tables, with any trailing prose around them."""
    names = set()
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 6 and cells[3] != "Branch":
            names.update(names_in(cells[3]))
    return frozenset(names)


def mentioned(names: list[str], text: str) -> frozenset[str]:
    found = names_in(text)
    return frozenset(name for name in names if name in found)


def protection(branch: Branch, evidence: Evidence) -> str | None:
    """Why the branch must stay whatever else is true (checks shared by both rules); None when nothing protects it."""
    if branch.name == DEFAULT_BRANCH:
        return "the default branch"
    if branch.name in evidence.keep_list:
        return f"keep list: {evidence.keep_list[branch.name]}"
    if branch.name in evidence.open_prs:
        return "an open pull request has it as its head"
    if (
        branch.name in evidence.register and not branch.merged
    ):  # a merged branch's row may be stale: the keep list holds it
        return "not merged, and named in docs/WORK_REGISTER.md's Branch column"
    return None


def merged_branch(branch: Branch, now: datetime) -> tuple[str, str]:
    landed = branch.landed_at or branch.tip_time
    if now - max(landed, branch.tip_time) < GRACE:
        return KEEP_UNSURE, "merged into main less than 24 h ago (grace for a late push)"
    return DELETE, "merged into main"


def ongoing_decision(branch: Branch, evidence: Evidence, now: datetime) -> tuple[str, str]:
    """The standing rule: a merged branch goes after the grace; everything else stays."""
    held = protection(branch, evidence)
    if held:
        return KEEP, held
    if branch.merged:
        return merged_branch(branch, now)
    if branch.name.startswith(REHEARSAL_PREFIX):
        return KEEP, REHEARSAL_WHY
    return KEEP, "not merged into main"


def inventory_decision(branch: Branch, evidence: Evidence, now: datetime) -> tuple[str, str]:
    """The one-off clean-up: the standing rule, plus idle unmerged branches (the owner accepts losing their commits)."""
    held = protection(branch, evidence)
    if held:
        return KEEP, held
    if branch.merged:
        return merged_branch(branch, now)
    if branch.name.startswith(REHEARSAL_PREFIX):
        return KEEP_UNSURE, REHEARSAL_WHY
    if now - branch.tip_time < RECENT:
        return KEEP_UNSURE, "not merged, last commit within 48 h, in no register row"
    if branch.work_files:
        return (
            KEEP_UNSURE,
            f"not merged; {branch.work_files} files of code, tests or captured data changed only here (owner decides)",
        )
    if branch.name in evidence.recent_mentions:
        return KEEP_UNSURE, "not merged; named in a file written in the last 48 h"
    return DELETE, f"not merged ({branch.ahead} commits only here), idle over 48 h, no open PR, in no register row"
