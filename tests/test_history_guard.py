"""Tests that read git history fail in a shallow clone with one message that says what to run (tests/history.py)."""

import subprocess

import pytest

from tests.history import SHALLOW, require_full_history


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_a_shallow_clone_fails_with_the_command_that_fixes_it_and_a_full_one_passes(tmp_path):
    origin = tmp_path / "origin"
    origin.mkdir()
    git(origin, "init", "-q")
    for n in (1, 2):
        (origin / "f.txt").write_text(str(n))
        git(origin, "add", "f.txt")
        git(origin, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", f"c{n}")
    git(tmp_path, "clone", "-q", "--depth", "1", f"file://{origin}", "shallow")
    with pytest.raises(pytest.fail.Exception, match=f"^{SHALLOW}$"):
        require_full_history(tmp_path / "shallow")
    require_full_history(origin)  # a full clone passes
