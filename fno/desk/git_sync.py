"""The daily run's git side (story E3; E1's across-containers rule). Cloud routines run in separate checkouts, and E1's
lock protects one machine only, so every account write runs as: pull, write under the book's `AccountLock`, commit,
push. If the push is rejected (another container pushed first), the unpushed local account commit is dropped, the
checkout is reset to the new `origin/<branch>` and the same fills are applied again: E1 makes them idempotent by fill
ID, so nothing is counted twice, and a plain pull would merge-conflict on `cash_ledger.csv` (judge 1).

The reset discards this checkout's unpushed work: run it only in the desk routine's own checkout, never a person's.
Commits run the repository's hooks (the public-record scan, O5): never `--no-verify`."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TypeVar

from ..books.paths import book_folder
from .daily_ports import AccountSync, Committer
from .records import DeskJournal

T = TypeVar("T")
PUSH_ATTEMPTS = 3


class GitError(RuntimeError):
    """A git step failed; the message names it."""


class Git:
    def __init__(self, root: Path, run=subprocess.run):
        self.root, self.run = Path(root), run

    def __call__(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        done = self.run(["git", *args], cwd=self.root, capture_output=True, text=True)
        if check and done.returncode != 0:
            raise GitError(f"git {' '.join(args[:2])} failed: {(done.stderr or done.stdout).strip()[-300:]}")
        return done

    def branch(self) -> str:
        return self("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()

    def commit_paths(self, paths: Sequence[Path], message: str) -> bool:
        """Adds and commits these paths; False when nothing changed."""
        relative = [Path(p).resolve().relative_to(self.root.resolve()).as_posix() for p in paths]
        self("add", "--", *relative)
        if self("diff", "--cached", "--quiet", check=False).returncode == 0:
            return False
        self("commit", "-q", "-m", message)
        return True

    def push(self) -> bool:
        return self("push", "-q", "origin", f"HEAD:{self.branch()}", check=False).returncode == 0


class GitCommitter(Committer):
    def __init__(self, git: Git):
        self.git = git

    def commit(self, paths: Sequence[Path], message: str) -> str:
        self.git("pull", "-q", "--no-rebase", "--no-edit", "origin", self.git.branch())
        if self.git.commit_paths(paths, message):
            for _ in range(PUSH_ATTEMPTS):
                if self.git.push():
                    break
                self.git("pull", "-q", "--no-rebase", "--no-edit", "origin", self.git.branch())
            else:
                raise GitError(f"push of '{message}' rejected {PUSH_ATTEMPTS} times")
        return self.git("rev-parse", "HEAD").stdout.strip()


class GitAccountSync(AccountSync):
    def __init__(self, git: Git, open_journal: Callable[[str], object]):
        self.git, self.open_journal = git, open_journal  # open_journal(book) -> the book's journal under its lock

    def write(self, book: str, apply: Callable[[DeskJournal], T], message: str) -> T:
        branch = self.git.branch()
        for _ in range(PUSH_ATTEMPTS):
            self.git("pull", "-q", "--no-rebase", "--no-edit", "origin", branch)
            with self.open_journal(book) as journal:
                result = apply(journal)
            if not self.git.commit_paths([book_folder(self.git.root, book)], message) or self.git.push():
                return result
            self.git("fetch", "-q", "origin", branch)
            self.git("reset", "-q", "--hard", f"origin/{branch}")  # drop the rejected account commit, apply again
        raise GitError(f"{book}: account push rejected {PUSH_ATTEMPTS} times; the fills are applied again next run")
