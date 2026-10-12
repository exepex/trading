"""Keeps a small local copy of the stock tool's research folders: a shallow, sparse git clone (about 10 MB)."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

GIT_TIMEOUT_SECONDS = 120
SHALLOW_SPARSE_CLONE = ("clone", "--quiet", "--depth", "1", "--filter=blob:none", "--sparse")


class ResearchRepoSync:
    def __init__(self, repo_url: str, local_path: Path, folders: list[str]):
        self.repo_url = repo_url
        self.local_path = local_path
        self.folders = folders

    def sync(self) -> bool:
        """Clone on first use, pull afterwards. Returns False (and keeps the old copy) if git fails."""
        try:
            if (self.local_path / ".git").exists():
                self._git("pull", "--quiet", "--depth", "1")
            else:
                self._clone()
            return True
        except (subprocess.SubprocessError, OSError) as exc:
            log.warning("research sync failed, using the existing copy: %s", exc)
            return False

    def _clone(self) -> None:
        self.local_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", *SHALLOW_SPARSE_CLONE, self.repo_url, str(self.local_path)],
            check=True,
            capture_output=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
        self._git("sparse-checkout", "set", *self.folders)

    def _git(self, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.local_path), *args], check=True, capture_output=True, timeout=GIT_TIMEOUT_SECONDS
        )
