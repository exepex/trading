"""The counts' commit (story MS-P1j; Judge B's note on judge 507.5): it adds and commits only the session's named
files, never the folder, so a stray file in the counts folder (a timed-out writer's `.<name>.part`) is never swept in.
A's `OwnedPathsCommitter` does the git work; this names the session's files inside the counts folder."""

from collections.abc import Sequence
from pathlib import Path, PurePosixPath

from ...storage.owned_paths_commit import OwnedPathsCommitter


class SessionFilesCommitter:
    def __init__(self, repository: Path, folder: Path, message: str):
        self.repository, self.folder, self.message = Path(repository), Path(folder), message

    def commit(self, what: str, paths: Sequence[str]) -> str:
        """`paths`: repository-relative files inside the counts folder."""
        inside = PurePosixPath(self.folder.resolve().relative_to(self.repository.resolve()).as_posix())
        owned = [PurePosixPath(p).relative_to(inside).as_posix() for p in paths]
        return OwnedPathsCommitter(self.repository, self.folder, owned, message=self.message).commit(what)
