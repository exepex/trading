"""The git side of a number claim (story O12): a temporary worktree of `origin/main`, one commit, one push.

The caller's own checkout (branch, index, working files) is never touched; the worktree is removed afterwards,
whether the claim worked or not.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from fno.numbering.categories import Category
from fno.numbering.registry import Row, read_rows

REMOTE = "origin"
BRANCH = "main"
TRACKING = f"refs/remotes/{REMOTE}/{BRANCH}"
FETCH_MAIN = ("fetch", "-q", REMOTE, f"+refs/heads/{BRANCH}:{TRACKING}")


class GitFailed(RuntimeError):
    """A git step other than the push failed (no network, no remote, no main): the claim stops."""


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and done.returncode != 0:
        raise GitFailed(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done


class MainCopy:
    """A detached worktree at the latest `main`, where a registry row is committed and pushed."""

    def __init__(self, path: Path):
        self.path = path

    def rows_of(self, category: Category) -> list[Row]:
        return read_rows(self.path / category.registry)

    def commit_and_push(self, registry: str, message: str) -> bool:
        """True when `main` accepted the push; False when it refused it (someone pushed first, or the push failed)."""
        _git(self.path, "add", "--", registry)
        _git(self.path, "commit", "-q", "-m", message, "--", registry)
        return _git(self.path, "push", "-q", REMOTE, f"HEAD:refs/heads/{BRANCH}", check=False).returncode == 0

    def reset_to_main(self) -> None:
        _git(self.path, *FETCH_MAIN)
        _git(self.path, "reset", "-q", "--hard", TRACKING)


class GitMain:
    """The repository whose `origin` holds the `main` that numbers are claimed on."""

    def __init__(self, repository: Path):
        self._repository = repository

    @contextmanager
    def main_copy(self) -> Iterator[MainCopy]:
        _git(self._repository, *FETCH_MAIN)
        place = Path(tempfile.mkdtemp(prefix="number-claim-"))
        _git(self._repository, "worktree", "add", "-q", "--detach", str(place), TRACKING)
        try:
            yield MainCopy(place)
        finally:
            _git(self._repository, "worktree", "remove", "--force", str(place), check=False)
            shutil.rmtree(place, ignore_errors=True)
            _git(self._repository, "worktree", "prune", check=False)
