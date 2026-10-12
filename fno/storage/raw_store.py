"""A store of large static files by name. Research scripts ask the stores first and the original source last."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ReadOnlyStoreError(RuntimeError):
    """Raised when a read-only store is asked to save a file."""


class RawFileStore(ABC):
    name: str = "store"

    @abstractmethod
    def get(self, filename: str) -> bytes | None:
        """The file's bytes, or None when the store does not have it."""

    @abstractmethod
    def put(self, filename: str, data: bytes) -> None:
        """Save a file (ReadOnlyStoreError if the store cannot)."""


class LocalFolderStore(RawFileStore):
    """A folder on disk; point it at a Google Drive for desktop folder and Drive uploads the files."""

    name = "local folder"

    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def get(self, filename: str) -> bytes | None:
        path = self.folder / filename
        return path.read_bytes() if path.is_file() else None

    def put(self, filename: str, data: bytes) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        temporary = self.folder / f".{filename}.part"
        temporary.write_bytes(data)
        temporary.replace(self.folder / filename)  # never leaves a half-written file under the real name
