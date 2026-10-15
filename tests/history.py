"""Tests that read git history (freeze commits, files as they were at a past commit) need the whole history. In a
shallow clone they would fail with a misleading error ("not in the history", a `git show` exit status 128, a different
hash), so they fail first, with one message that says what to do. A failure, never a skip: the check still has to be
run."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

SHALLOW = "shallow clone: run git fetch --unshallow origin main"


def require_full_history(root: Path) -> None:
    shallow = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"], cwd=root, capture_output=True, text=True, check=True
    )
    if shallow.stdout.strip() == "true":
        pytest.fail(SHALLOW, pytrace=False)
