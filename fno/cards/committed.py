"""The card reads committed records only (story T1 criterion 5): `GitHeadRecords` reads a file's bytes as committed at
`HEAD`, so an edited or untracked file in the working tree can never reach a card."""

from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path


class CommittedRecords(ABC):
    @abstractmethod
    def read(self, path: str) -> bytes | None:
        """The committed bytes of a repository path, or None when it is not committed."""

    @abstractmethod
    def names(self, folder: str) -> list[str]:
        """The committed file names directly inside a folder, sorted ([] when there is none)."""


class GitHeadRecords(CommittedRecords):
    def __init__(self, root: Path, commit: str = "HEAD"):
        self.root, self.commit = Path(root), commit

    def _git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True)

    def read(self, path: str) -> bytes | None:
        shown = self._git("show", f"{self.commit}:{path}")
        return shown.stdout if shown.returncode == 0 else None

    def names(self, folder: str) -> list[str]:
        listed = self._git("ls-tree", "--name-only", self.commit, f"{folder.rstrip('/')}/")
        if listed.returncode != 0:
            return []
        return sorted(Path(line).name for line in listed.stdout.decode("utf-8").splitlines() if line)

    def code_commit(self) -> str:
        return self._git("rev-parse", self.commit).stdout.decode("utf-8").strip()
