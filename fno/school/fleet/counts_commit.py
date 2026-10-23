"""The run's single commit (story MS-P1j; Judge B's note on judge 507.5, judge 523): it adds and commits exactly the
session's named files, never a folder, so a stray file (a writer's `.<name>.part`) is never swept in. The names may sit
anywhere in the checkout: the counts, and the instructor's counts file and receipts, which its step wrote on the run's
own thread (one committer per run). O9's `GitManifestRecorder` does the git work (pull, push, the hook check)."""

from collections.abc import Sequence
from pathlib import Path

from ...storage.manifest_commit import GitManifestRecorder

LABEL = "school session files"


class NamedFiles(GitManifestRecorder):
    """Exactly `files` (repository-relative), those that exist or are tracked: Git refuses a whole `add` when one
    pathspec matches nothing."""

    def __init__(self, repository: Path, files: Sequence[str], message: str):
        super().__init__(repository, repository, message=message, label=LABEL)
        self.files = tuple(files)

    def owns(self, path: str) -> bool:
        return path in self.files

    def _paths(self) -> list[str]:
        listed = self._git("ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *self.files)
        present = set(listed.stdout.split("\0"))
        return [name for name in self.files if name in present]


class SessionFilesCommitter:
    def __init__(self, repository: Path, message: str):
        self.repository, self.message = Path(repository), message

    def commit(self, what: str, paths: Sequence[str]) -> str:
        """`paths`: repository-relative files."""
        return NamedFiles(self.repository, paths, self.message).commit(what)
