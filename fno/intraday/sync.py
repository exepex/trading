"""The recorder's link to the repository (story A16): pull before settling marks, so a run sees the rows the other
overlapping run pushed, and commit after each mark. Two checkouts write one-file-per-record folders; a same-file clash
keeps the copy already on GitHub (the first push). A dry run uses `NoSync`: nothing pulled, committed or pushed."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..storage.manifest_commit import GitManifestRecorder

PULLED = "pulled main"
NOT_PULLED = "pull failed, settling from this checkout as it is: {reason}"
NOT_PUBLISHED = "dry run: nothing pulled, committed or pushed"


class LedgerSync(ABC):
    @abstractmethod
    def pull(self) -> str:
        """Brings in what other runs pushed; a one-line outcome (never raises)."""

    @abstractmethod
    def commit(self, what: str) -> str:
        """Commits and pushes this folder; a one-line outcome (never raises, never bypasses a hook)."""


class GitLedgerSync(LedgerSync):
    def __init__(self, committer: GitManifestRecorder):
        self.committer = committer

    def pull(self) -> str:
        pulled = self.committer.pull()
        if pulled.returncode == 0:
            return PULLED
        self.committer.abort_merge()
        text = (pulled.stderr or pulled.stdout or "").strip()
        return NOT_PULLED.format(reason=text.splitlines()[0] if text else f"exit code {pulled.returncode}")

    def commit(self, what: str) -> str:
        return self.committer.commit(what)


class NoSync(LedgerSync):
    def pull(self) -> str:
        return NOT_PUBLISHED

    def commit(self, what: str) -> str:
        return NOT_PUBLISHED
