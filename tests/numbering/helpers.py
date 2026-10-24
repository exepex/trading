"""Shared fixtures for the number-claim tests (story O12): small checkouts and real git repositories."""

from __future__ import annotations

import subprocess
from pathlib import Path

HEADER = "number,name,session,claimed_at_utc\n"


def write(root: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def origin_and_clones(tmp_path: Path, files: dict[str, str], clones: int = 2) -> list[Path]:
    """A bare `origin` whose `main` holds the files, and that many clones of it."""
    seed = tmp_path / "seed"
    seed.mkdir()
    git(seed, "init", "-q", "-b", "main")
    _identity(seed)
    write(seed, files)
    git(seed, "add", "-A")
    git(seed, "commit", "-q", "-m", "seed")
    git(tmp_path, "clone", "-q", "--bare", str(seed), "origin.git")
    copies = []
    for n in range(clones):
        git(tmp_path, "clone", "-q", "origin.git", f"clone{n}")
        _identity(tmp_path / f"clone{n}")
        copies.append(tmp_path / f"clone{n}")
    return copies


def origin_file(tmp_path: Path, name: str) -> str:
    return git(tmp_path / "origin.git", "show", f"main:{name}")


def _identity(repo: Path) -> None:
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "test")
    git(repo, "config", "core.hooksPath", "/dev/null")
