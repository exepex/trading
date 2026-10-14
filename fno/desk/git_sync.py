"""The daily run's git side (story E3; E1's across-containers rule). Cloud routines run in separate checkouts, and E1's
lock protects one machine only, so every account write runs as: pull, write under the book's `AccountLock`, commit,
push. If the push is rejected (another container pushed first), the unpushed local account commit is dropped, the
checkout is reset to the new `origin/<branch>` and the same fills are applied again: E1 makes them idempotent by fill
ID, so nothing is counted twice, and a plain pull would merge-conflict on `cash_ledger.csv` (judge 1).

A reset must never destroy other work (judge 82), so "a dedicated checkout" is checked, not assumed: an account write
is refused unless the tracked worktree is clean and nothing is unpushed, and before any reset it confirms that the only
commit ahead of the pulled origin is this write's own; otherwise it stops and alerts #fno-desk.
Commits run the repository's hooks (the public-record scan, O5): never `--no-verify`."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TypeVar

from ..alerts.sender import AlertSender
from ..books.paths import book_folder
from .daily_ports import AccountSync, Committer
from .records import DeskJournal

T = TypeVar("T")
PUSH_ATTEMPTS = 3


class GitError(RuntimeError):
    """A git step failed; the message names it."""


class CheckoutNotDedicated(GitError):
    """The checkout holds other work (uncommitted tracked edits or unpushed commits): no account write, no reset."""


DIRTY = "{book}: account write refused: the checkout holds other work ({what}); it is never reset over"
UNEXPECTED = "{book}: rejected push NOT reset: {count} commit(s) ahead, not only this write's; resolve by hand"


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

    def other_work(self) -> str:
        """What a reset would destroy here, besides nothing: uncommitted tracked edits, or commits not on origin."""
        if self("status", "--porcelain", "--untracked-files=no").stdout.strip():
            return "uncommitted tracked edits"
        self("fetch", "-q", "origin", self.branch())
        ahead = self("rev-list", f"origin/{self.branch()}..HEAD").stdout.split()
        return f"{len(ahead)} unpushed commit(s)" if ahead else ""

    def ahead_of(self, commit: str) -> list[str]:
        return self("rev-list", f"{commit}..HEAD").stdout.split()


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
    def __init__(self, git: Git, open_journal: Callable[[str], object], alerts: AlertSender):
        self.git, self.open_journal, self.alerts = git, open_journal, alerts  # open_journal(book): under its lock

    def write(self, book: str, apply: Callable[[DeskJournal], T], message: str) -> T:
        branch = self.git.branch()
        for _ in range(PUSH_ATTEMPTS):
            self._require_dedicated(book)
            self.git("pull", "-q", "--no-rebase", "--no-edit", "origin", branch)
            pulled = self.git("rev-parse", "HEAD").stdout.strip()
            with self.open_journal(book) as journal:
                result = apply(journal)
            if not self.git.commit_paths([book_folder(self.git.root, book)], message) or self.git.push():
                return result
            ahead = self.git.ahead_of(pulled)
            if len(ahead) != 1:  # only this write's commit may be dropped
                self._stop(UNEXPECTED.format(book=book, count=len(ahead)))
            self.git("fetch", "-q", "origin", branch)
            self.git("reset", "-q", "--hard", f"origin/{branch}")  # drop the rejected account commit, apply again
        raise GitError(f"{book}: account push rejected {PUSH_ATTEMPTS} times; the fills are applied again next run")

    def _require_dedicated(self, book: str) -> None:
        other = self.git.other_work()
        if other:
            self._stop(DIRTY.format(book=book, what=other))

    def _stop(self, text: str) -> None:
        self.alerts.send(text)
        raise CheckoutNotDedicated(text)
