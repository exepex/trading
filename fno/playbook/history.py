"""The git questions the playbook asks (story D1): B4's `Git` adapter plus the commits that changed one file."""

from __future__ import annotations

from typing import Protocol

from ..research_engine.ledger import Git


class History(Protocol):
    def commit_exists(self, commit: str) -> bool: ...

    def is_ancestor(self, older: str, newer: str) -> bool: ...

    def committed_text(self, path: str, commit: str = "HEAD") -> str | None: ...

    def head(self) -> str: ...


class PlaybookGit(Git):
    def commits_touching(self, path: str) -> list[str]:
        """Every commit that changed `path`, oldest first (all of history: a shallow clone shows only its part)."""
        return self._run("log", "--format=%H", "--reverse", "--", path).stdout.split()

    def file_versions(self, path: str) -> list[str]:
        """The committed texts of `path`, oldest first."""
        texts = (self.committed_text(path, commit) for commit in self.commits_touching(path))
        return [text for text in texts if text is not None]
