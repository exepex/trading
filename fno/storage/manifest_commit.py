"""Makes manifest rows durable (story A10 follow-up): rows written at save time live in the repository's working tree
until committed, and a fresh checkout without them would report the saved files as unfingerprinted. After every
librarian run the rows are committed and pushed; `data-coverage` reports any that are still uncommitted.

The commit runs the repository's hooks (the public-record scan, story O5): a refused commit is reported, never
bypassed (no `--no-verify`). The branch is pulled with `--no-rebase` before pushing (CLAUDE.md: others push to it too).
"""

from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

COMMIT_MESSAGE = "Manifests: SHA-256 rows written at save time ({what})"
COMMITTED = "manifest rows committed and pushed ({count} file(s))"
NOTHING = "manifest rows: nothing new to commit"
NOT_COMMITTED = "manifest rows NOT committed: {step} failed: {reason}. Commit research/data/manifests/ by hand"


class ManifestRecorder(ABC):
    @abstractmethod
    def pending(self) -> list[str]:
        """Manifest files with rows not yet committed (empty when everything is committed)."""

    @abstractmethod
    def commit(self, what: str) -> str:
        """Commits and pushes the pending manifests; a one-line outcome (never raises, never bypasses a hook)."""


class GitManifestRecorder(ManifestRecorder):
    def __init__(self, repository: Path, folder: Path, run=subprocess.run):
        self.repository, self.run = Path(repository), run
        self.folder = Path(folder).resolve().relative_to(self.repository.resolve()).as_posix()

    def _git(self, *args: str) -> subprocess.CompletedProcess:
        return self.run(["git", *args], cwd=self.repository, capture_output=True, text=True)

    def pending(self) -> list[str]:
        status = self._git("status", "--porcelain", "--untracked-files=all", "--", self.folder)
        return sorted(line[3:] for line in status.stdout.splitlines() if line.strip())

    def commit(self, what: str) -> str:
        files = self.pending()
        if not files:
            return NOTHING
        steps = (
            ("add", ("add", "--", self.folder)),
            ("commit", ("commit", "-m", COMMIT_MESSAGE.format(what=what), "--", self.folder)),
            ("pull", ("pull", "--no-rebase", "--no-edit", "origin", self._branch())),
            ("push", ("push", "origin", "HEAD")),
        )
        for step, args in steps:
            result = self._git(*args)
            if result.returncode != 0:
                return NOT_COMMITTED.format(step=step, reason=_first_line(result))
        return COMMITTED.format(count=len(files))

    def _branch(self) -> str:
        return self._git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def _first_line(result: subprocess.CompletedProcess) -> str:
    text = (result.stderr or result.stdout or "").strip()
    return text.splitlines()[0] if text else f"exit code {result.returncode}"
