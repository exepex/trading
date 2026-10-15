"""The daily run's git side (story E3; E1's across-containers rule). Cloud routines run in separate checkouts, and E1's
lock protects one machine only, so every account write runs as: pull, write under the book's `AccountLock`, commit,
push. If the push is rejected (another container pushed first), the unpushed local account commit is dropped, the
checkout is reset to the new `origin/<branch>` and the same fills are applied again: E1 makes them idempotent by fill
ID, so nothing is counted twice, and a plain pull would merge-conflict on `cash_ledger.csv` (judge 1).

A reset must never destroy other work (judge 82), so "a dedicated book folder" is checked, not assumed (judge 82
addendum 6): an account write is refused while anything is unpushed or this book's folder holds uncommitted work
(tracked edits or new files: the commit adds the whole folder and must not sweep in another writer's partial work).
Edits elsewhere in the checkout do not refuse it, so one book's leftover never stops the others. Before any reset it
confirms that the only commit ahead of the pulled origin is this write's own, and the reset is `--keep`: git keeps the
edits it does not touch and refuses rather than overwrite one; any refusal stops and alerts #fno-desk.
Commits run the repository's hooks (the public-record scan, O5): never `--no-verify`."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TypeVar

from ..alerts.sender import AlertSender
from ..books.paths import book_folder
from ..config import ROOT
from ..storage.wiring import QUOTES_FOLDER
from .commit_guard import RawQuoteCommitRefused, RawQuoteGuard
from .daily_ports import AccountSync, AccountWriteRefused, Committer
from .records import DeskJournal

T = TypeVar("T")
PUSH_ATTEMPTS = 3


class GitError(AccountWriteRefused):
    """A git step failed; the message names it. For the daily run, any git failure refuses that account write."""


class CheckoutNotDedicated(GitError):
    """Other work is in the way (unpushed commits, uncommitted work in the book's folder, or an edit a reset would
    overwrite): no account write, no reset."""


DIRTY = "{book}: account write refused: the checkout holds other work ({what}); it is never reset over"
UNEXPECTED = "{book}: rejected push NOT reset: {count} commit(s) ahead, not only this write's; resolve by hand"
NOT_KEPT = "{book}: rejected push NOT reset: the reset would overwrite a local edit ({error}); resolve by hand"


class Git:
    def __init__(self, root: Path, run=subprocess.run, guard: RawQuoteGuard | None = None):
        self.root, self.run = Path(root), run
        self.guard = guard or RawQuoteGuard(self.root, self.root / QUOTES_FOLDER.relative_to(ROOT))

    def __call__(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        done = self.run(["git", *args], cwd=self.root, capture_output=True, text=True)
        if check and done.returncode != 0:
            raise GitError(f"git {' '.join(args[:2])} failed: {(done.stderr or done.stdout).strip()[-300:]}")
        return done

    def branch(self) -> str:
        return self("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()

    def commit_paths(self, paths: Sequence[Path], message: str) -> bool:
        """Adds and commits these paths; False when nothing changed. What would be committed is the whole index, so
        the raw-quote guard checks every staged file after the add (a folder or a pathspec expands there, and a file
        staged earlier by anything else is seen too); on a refusal this add is undone (another writer's staged files are
        left as they were, so the next commit refuses too) and nothing is committed."""
        self.guard.check(paths)
        added = [self.relative(p) for p in paths]
        self("add", "--", *added)
        staged = self("diff", "--cached", "--name-only", "-z").stdout.split("\0")
        try:
            self.guard.check([self.root / name for name in staged if name])
        except RawQuoteCommitRefused:
            self("reset", "-q", "--", *added, check=False)
            raise
        if self("diff", "--cached", "--quiet", check=False).returncode == 0:
            return False
        self("commit", "-q", "-m", message)
        return True

    def push(self) -> bool:
        return self("push", "-q", "origin", f"HEAD:{self.branch()}", check=False).returncode == 0

    def relative(self, path: Path) -> str:
        return Path(path).resolve().relative_to(self.root.resolve()).as_posix()

    def other_work(self, folder: Path) -> str:
        """What an account write in `folder` could sweep in or lose: uncommitted work in the folder (ignored files
        aside), or commits not on origin; empty when there is none."""
        if self("status", "--porcelain", "--untracked-files=all", "--", self.relative(folder)).stdout.strip():
            return f"uncommitted work in {self.relative(folder)}"
        self("fetch", "-q", "origin", self.branch())
        ahead = self("rev-list", f"origin/{self.branch()}..HEAD").stdout.split()
        return f"{len(ahead)} unpushed commit(s)" if ahead else ""

    def ahead_of(self, commit: str) -> list[str]:
        return self("rev-list", f"{commit}..HEAD").stdout.split()


class GitCommitter(Committer):
    """Every commit passes `RawQuoteGuard` (story E2b): first on the given paths, before git runs (not even the pull),
    then on everything staged (`Git.commit_paths`)."""

    def __init__(self, git: Git):
        self.git = git

    def commit(self, paths: Sequence[Path], message: str) -> str:
        self.git.guard.check(paths)
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
        branch, folder = self.git.branch(), book_folder(self.git.root, book)
        for _ in range(PUSH_ATTEMPTS):
            self._require_dedicated(book, folder)
            self.git("pull", "-q", "--no-rebase", "--no-edit", "origin", branch)
            pulled = self.git("rev-parse", "HEAD").stdout.strip()
            with self.open_journal(book) as journal:
                result = apply(journal)
            if not self.git.commit_paths([folder], message) or self.git.push():
                return result
            ahead = self.git.ahead_of(pulled)
            if len(ahead) != 1:  # only this write's commit may be dropped
                self._stop(UNEXPECTED.format(book=book, count=len(ahead)))
            self.git("fetch", "-q", "origin", branch)
            self._reset_keeping_edits(book, f"origin/{branch}")  # drop the rejected account commit, apply again
        raise GitError(f"{book}: account push rejected {PUSH_ATTEMPTS} times; the fills are applied again next run")

    def _require_dedicated(self, book: str, folder: Path) -> None:
        other = self.git.other_work(folder)
        if other:
            self._stop(DIRTY.format(book=book, what=other))

    def _reset_keeping_edits(self, book: str, target: str) -> None:
        done = self.git("reset", "-q", "--keep", target, check=False)
        if done.returncode != 0:
            self._stop(NOT_KEPT.format(book=book, error=(done.stderr or done.stdout).strip()[-200:]))

    def _stop(self, text: str) -> None:
        self.alerts.send(text)
        raise CheckoutNotDedicated(text)
