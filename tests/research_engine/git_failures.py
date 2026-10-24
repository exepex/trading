"""Every git call of an action failing in turn (story git-before-writes): the action is run once to count its git
calls, then once per call on a fresh repository with that one call failing (exit 128, as a broken repository). Each
run must raise and leave every file of the working tree as it was: no git read may come after the first write."""

import hashlib
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from fno.research_engine.ledger import GitFailed

REAL = subprocess.run
BROKEN = "fatal: unable to read tree (simulated: out of memory)"


class GitCalls:
    """Counts git calls; with `fail_at`, that one call (0-based) fails."""

    def __init__(self, fail_at: int | None = None):
        self.count, self.fail_at = 0, fail_at

    def __call__(self, args, *a, **k):
        if args[:1] == ["git"]:
            self.count += 1
            if self.count - 1 == self.fail_at:
                return subprocess.CompletedProcess(args, 128, "", BROKEN)
        return REAL(args, *a, **k)


def tree(root: Path) -> dict[str, str]:
    """Every working-tree file outside .git, by its SHA-256."""
    files = (p for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts)
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def calls_of(monkeypatch, root: Path, act: Callable[[Path], object]) -> int:
    counter = GitCalls()
    with monkeypatch.context() as patch:
        patch.setattr(subprocess, "run", counter)
        act(root)
    return counter.count


def require_nothing_written_on_any_git_failure(monkeypatch, tmp_path: Path, build: Callable[[Path], Path],
                                               act: Callable[[Path], object]) -> int:  # fmt: skip
    """`build(folder)` makes a fresh repository; `act(root)` is the action. Returns how many git calls were checked."""
    count = calls_of(monkeypatch, build(tmp_path / "count"), act)
    assert count > 0
    for failing in range(count):
        root = build(tmp_path / f"fail-{failing}")
        before = tree(root)
        with monkeypatch.context() as patch:
            patch.setattr(subprocess, "run", GitCalls(failing))
            with pytest.raises(GitFailed):
                act(root)
        assert tree(root) == before, f"git call {failing} of {count} failed after a write"
    return count
