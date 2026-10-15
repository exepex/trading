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
from .daily_ports import AccountSync, AccountWriteRefused, CommitFailed, Committer
from .records import DeskJournal

T = TypeVar("T")
PUSH_ATTEMPTS = 3


class GitError(AccountWriteRefused):
    """A git step failed; the message names it. For the daily run, any git failure refuses that account write."""


class PushRejected(GitError):
    """Every push attempt was rejected: the commit stays local and unpushed."""


class CheckoutNotDedicated(GitError):
    """Other work is in the way (unpushed commits, uncommitted work in the book's folder, or an edit a reset would
    overwrite): no account write, no reset."""


DIRTY = "{book}: account write refused: the checkout holds other work ({what}); it is never reset over"
STRAY = "the checkout holds {count} unpushed commit(s) the run did not make ({what}); never pushed: resolve by hand"
UNEXPECTED = "{book}: rejected push NOT reset: {count} commit(s) ahead, not only this write's; resolve by hand"
RAW_STAGED = "{book}: account write refused before any fill was applied: {reason}"
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
        try:
            self.guard.check(self.staged())
        except RawQuoteCommitRefused:
            self("reset", "-q", "--", *added, check=False)
            raise
        if self("diff", "--cached", "--quiet", check=False).returncode == 0:
            return False
        self("commit", "-q", "-m", message)
        return True

    def staged(self) -> list[Path]:
        """Every path in the index that differs from HEAD (a staged deletion too): what the next commit would carry."""
        names = self("diff", "--cached", "--name-only", "-z").stdout.split("\0")
        return [self.root / name for name in names if name]

    def push(self) -> bool:
        return self("push", "-q", "origin", f"HEAD:{self.branch()}", check=False).returncode == 0

    def relative(self, path: Path) -> str:
        return Path(path).resolve().relative_to(self.root.resolve()).as_posix()

    def other_work(self, folder: Path) -> str:
        """What an account write in `folder` could sweep in or lose: uncommitted work in the folder (ignored files
        aside), or commits not on origin; empty when there is none."""
        if self("status", "--porcelain", "--untracked-files=all", "--", self.relative(folder)).stdout.strip():
            return f"uncommitted work in {self.relative(folder)}"
        ahead = self.unpushed()
        return f"{len(ahead)} unpushed commit(s)" if ahead else ""

    def unpushed(self, *options: str) -> list[str]:
        """Commits on HEAD that origin does not have (after a fetch): what a push would publish. The one rule both the
        account writes and the run's commits start from (decision 51)."""
        self("fetch", "-q", "origin", self.branch())
        return self.ahead_of(f"origin/{self.branch()}", *options)

    def unpushed_files(self) -> list[Path]:
        """Every file a push would change on origin (a deletion too), whoever made the commits."""
        names = self("diff", "--name-only", "-z", f"origin/{self.branch()}", "HEAD").stdout.split("\0")
        return [self.root / name for name in names if name]

    def subject(self, commit: str) -> str:
        return self("show", "-s", "--format=%s", commit).stdout.strip()

    def files_of(self, commit: str) -> set[str]:
        names = self("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit).stdout.split("\0")
        return {name for name in names if name}

    def ahead_of(self, commit: str, *options: str) -> list[str]:
        return self("rev-list", *options, f"{commit}..HEAD").stdout.split()


class GitCommitter(Committer):
    """Every commit passes `RawQuoteGuard` (story E2b): first on the given paths, before git runs (not even the pull),
    then on everything staged (`Git.commit_paths`), and before every push on every file the push would change. An
    unpushed commit the run did not make is refused before the pull (decision 51): the only one allowed is the run's
    own `own_unpushed` commit, known by its message and by touching only these paths. Any refusal or git failure is
    raised as `CommitFailed`."""

    def __init__(self, git: Git):
        self.git = git

    def commit(self, paths: Sequence[Path], message: str, own_unpushed: str = "") -> str:
        try:
            return self._commit(paths, message, own_unpushed)
        except (RawQuoteCommitRefused, GitError) as failure:
            raise CommitFailed(str(failure), unpushed=isinstance(failure, PushRejected)) from failure

    def _commit(self, paths: Sequence[Path], message: str, own_unpushed: str) -> str:
        self.git.guard.check(paths)
        self._refuse_stray(paths, own_unpushed)
        branch = self.git.branch()
        self.git("pull", "-q", "--no-rebase", "--no-edit", "origin", branch)
        if self.git.commit_paths(paths, message) or self.git.ahead_of(f"origin/{branch}"):  # or one left unpushed
            for _ in range(PUSH_ATTEMPTS):
                self.git.guard.check(self.git.unpushed_files())
                if self.git.push():
                    break
                self.git("pull", "-q", "--no-rebase", "--no-edit", "origin", branch)
            else:
                raise PushRejected(
                    f"push of '{message}' rejected {PUSH_ATTEMPTS} times; the commit stays local, unpushed"
                )
        return self.git("rev-parse", "HEAD").stdout.strip()

    def _refuse_stray(self, paths: Sequence[Path], own_unpushed: str) -> None:
        """A merge made by a retry's pull is not a stray: what it brings in is checked commit by commit here, and every
        file it changes on origin by the guard before the push."""
        names = {self.git.relative(p) for p in paths}
        stray = [c for c in self.git.unpushed("--no-merges") if not self._own(c, own_unpushed, names)]
        if stray:
            what = "; ".join(f"'{self.git.subject(c)}': {', '.join(sorted(self.git.files_of(c)))}" for c in stray)
            raise GitError(STRAY.format(count=len(stray), what=what))

    def _own(self, commit: str, own_unpushed: str, names: set[str]) -> bool:
        return bool(own_unpushed) and self.git.subject(commit) == own_unpushed and self.git.files_of(commit) <= names


class GitAccountSync(AccountSync):
    def __init__(self, git: Git, open_journal: Callable[[str], object], alerts: AlertSender):
        self.git, self.open_journal, self.alerts = git, open_journal, alerts  # open_journal(book): under its lock

    def write(self, book: str, apply: Callable[[DeskJournal], T], message: str) -> T:
        branch, folder = self.git.branch(), book_folder(self.git.root, book)
        for _ in range(PUSH_ATTEMPTS):
            self._require_dedicated(book, folder)
            self._require_no_raw_quote_staged(book)
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

    def _require_no_raw_quote_staged(self, book: str) -> None:
        """Checked before anything is applied (judge 118 addendum 2): a raw quote file already in the index would be
        swept into this account commit, so the write is refused as one the desk handles ("not filled", an alert, the
        other books and the exits go on) and the journal is left exactly as it was. The account writer itself never
        copies a raw file, so after this check the add of the book folder cannot stage one."""
        try:
            self.git.guard.check(self.git.staged())
        except RawQuoteCommitRefused as refused:
            self._stop(RAW_STAGED.format(book=book, reason=refused))

    def _reset_keeping_edits(self, book: str, target: str) -> None:
        done = self.git("reset", "-q", "--keep", target, check=False)
        if done.returncode != 0:
            self._stop(NOT_KEPT.format(book=book, error=(done.stderr or done.stdout).strip()[-200:]))

    def _stop(self, text: str) -> None:
        self.alerts.send(text)
        raise CheckoutNotDedicated(text)
