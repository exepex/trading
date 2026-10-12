"""A store of large static files, addressed by a relative path that follows the archive layout
(`<area>/<publisher>/<market>/<dataset>/<YYYY>/<MM>/<original file name>` under one project folder, see
fno/storage/README.md).

Raw files never change: saving the same bytes again is a no-op, and different bytes at an existing path are refused.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path, PurePosixPath


class ReadOnlyStoreError(RuntimeError):
    """Raised when a read-only store is asked to save a file."""


class RawFileConflict(RuntimeError):
    """A different file already exists at that path (or the path is ambiguous); nothing was overwritten."""


def path_parts(path: str) -> list[str]:
    """The folders and file name of an archive path; refuses absolute paths, '..' and empty parts."""
    parts = path.split("/")
    if not path or PurePosixPath(path).is_absolute() or any(p in ("", ".", "..") for p in parts):
        raise ValueError(f"not a valid archive path: {path!r}")
    return parts


class RawFileStore(ABC):
    name: str = "store"

    @abstractmethod
    def get(self, path: str) -> bytes | None:
        """The file's bytes, or None when the store does not have it."""

    @abstractmethod
    def put(self, path: str, data: bytes) -> None:
        """Save a file (ReadOnlyStoreError if the store cannot, RawFileConflict if different bytes are there)."""


class LocalFolderStore(RawFileStore):
    """A folder on disk; point it at a Google Drive for desktop folder and Drive uploads the same tree."""

    name = "local folder"

    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def _file(self, path: str) -> Path:
        return self.folder.joinpath(*path_parts(path))

    def get(self, path: str) -> bytes | None:
        file = self._file(path)
        return file.read_bytes() if file.is_file() else None

    def put(self, path: str, data: bytes) -> None:
        file = self._file(path)
        if file.is_file():
            if file.read_bytes() != data:
                raise RawFileConflict(f"{path} already exists with different content")
            return
        file.parent.mkdir(parents=True, exist_ok=True)
        temporary = file.with_name(f".{file.name}.part")
        temporary.write_bytes(data)
        temporary.replace(file)  # never leaves a half-written file under the real name


class AreaStore(RawFileStore):
    """One area (sub-folder such as `raw`) of a store rooted at the project folder, so every kind of file has its own
    branch and nothing lands loose in the project folder. Wraps any store; the store itself never knows."""

    def __init__(self, store: RawFileStore, area: str):
        path_parts(area)  # validates the area name
        self.store, self.area = store, area
        self.name = store.name

    def get(self, path: str) -> bytes | None:
        return self.store.get(f"{self.area}/{path}")

    def put(self, path: str, data: bytes) -> None:
        self.store.put(f"{self.area}/{path}", data)
