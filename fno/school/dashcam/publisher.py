"""Pushing a receipt to the remote, the second half of a seal (story 3.4): a seal exists only once the receipt of the
saved file is on `main`, so a fill can name a seal that others can see."""

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from ...storage.manifest_commit import TARGET_BRANCH, ManifestRecorder
from ...storage.receipts import Receipt, ReceiptFolder

COMMIT_FORMAT = "%H %cI"  # commit id, committer time (the pushed commit's own time is the seal's pushed_at)
NOT_ON_REMOTE = "the receipt of {path} is not on {target} ({outcome})"


class SealNotPushed(Exception):
    """The receipt could not be committed and pushed: the file has no seal and nothing may fill on it."""


@dataclass(frozen=True)
class PushedReceipt:
    commit: str
    pushed_at: datetime  # the commit's own time: never later than the push, so a seal is never dated early
    sha256: str  # the SHA-256 the receipt holds in that commit


@runtime_checkable
class ReceiptPublisher(Protocol):
    def publish(self, drive_path: str, what: str) -> PushedReceipt:
        """Commit and push the receipts, then name the commit on the remote that holds this file's receipt
        (`SealNotPushed` when there is none). Called again for a receipt already pushed, it names the same commit."""

    def published(self, drive_path: str) -> PushedReceipt | None:
        """The commit on the remote that added this file's receipt, with the SHA-256 it holds there, or None."""


class GitReceiptPublisher:
    def __init__(self, recorder: ManifestRecorder, receipts: ReceiptFolder, repository: Path, run=subprocess.run):
        self.recorder, self.receipts, self.repository, self.run = recorder, receipts, Path(repository), run

    def publish(self, drive_path: str, what: str) -> PushedReceipt:
        outcome = self.recorder.commit(what)
        found = self.published(drive_path) or self._push_unpushed(drive_path)
        if found is None:
            raise SealNotPushed(NOT_ON_REMOTE.format(path=drive_path, target=TARGET_BRANCH, outcome=outcome))
        return found

    def published(self, drive_path: str) -> PushedReceipt | None:
        self._git("fetch", "origin", TARGET_BRANCH)
        file = self.receipts.file_for(drive_path).relative_to(self.repository).as_posix()
        added = self._git("log", f"origin/{TARGET_BRANCH}", "--diff-filter=A", "-1", f"--format={COMMIT_FORMAT}",
                          "--", file)  # fmt: skip
        if added.returncode != 0 or not added.stdout.strip():
            return None
        commit, when = added.stdout.split()
        text = self._git("show", f"{commit}:{file}")
        if text.returncode != 0:
            return None
        return PushedReceipt(commit, datetime.fromisoformat(when), Receipt.from_text(drive_path, text.stdout).sha256)

    def _push_unpushed(self, drive_path: str) -> PushedReceipt | None:
        """A receipt committed by an earlier run whose push failed: nothing is pending, so push it now."""
        if self.recorder.pull().returncode != 0:
            self.recorder.abort_merge()
            return None
        self._git("push", "origin", f"HEAD:{TARGET_BRANCH}")
        return self.published(drive_path)

    def _git(self, *args: str) -> subprocess.CompletedProcess:
        return self.run(["git", *args], cwd=self.repository, capture_output=True, text=True)
