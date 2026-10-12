"""Which files the public-record scan reads (story O5): the committed records, the records staged for a routine's
commit, or files named explicitly (a session export before it is sent)."""

from __future__ import annotations

import gzip
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

# Code folders: they hold the scan's own patterns and the tests' planted values. Everything else tracked is a record,
# so a new record folder (journal/, playbook/, agents/, book3/ ...) is scanned without being listed anywhere.
CODE_FOLDERS = ("fno/", "tests/", "tools/")
TRACKED_FILES = ("git", "ls-files", "-z")
STAGED_FILES = ("git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR")
STAGED_BLOB = ("git", "show")  # + ":<path>": the staged bytes, which are what the commit will hold


@dataclass(frozen=True)
class RecordText:
    path: str
    text: str


def as_text(path: str, data: bytes) -> str:
    """The file's text; gzip files are unpacked first (their content is committed too)."""
    if path.endswith(".gz"):
        data = gzip.decompress(data)
    return data.decode("utf-8", errors="replace")


def is_record(path: str) -> bool:
    return not path.startswith(CODE_FOLDERS)


class RecordSource(ABC):
    @abstractmethod
    def records(self) -> Iterator[RecordText]:
        """Each file to scan, with its text."""


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(args, cwd=root, check=True, capture_output=True).stdout


def _paths(output: bytes) -> list[str]:
    return [p for p in output.decode("utf-8").split("\0") if p]


class TrackedRecords(RecordSource):
    """Every record git tracks, as it is in the working tree."""

    def __init__(self, root: Path):
        self._root = root

    def records(self) -> Iterator[RecordText]:
        for path in filter(is_record, _paths(_git(self._root, *TRACKED_FILES))):
            file = self._root / path
            if file.is_file():  # deleted in the working tree but not yet in the index
                yield RecordText(path, as_text(path, file.read_bytes()))


class StagedRecords(RecordSource):
    """The records staged for the next commit, exactly as the commit will hold them."""

    def __init__(self, root: Path):
        self._root = root

    def records(self) -> Iterator[RecordText]:
        for path in filter(is_record, _paths(_git(self._root, *STAGED_FILES))):
            yield RecordText(path, as_text(path, _git(self._root, *STAGED_BLOB, f":{path}")))


class NamedFiles(RecordSource):
    """Files named on the command line (whole folders included), wherever they are."""

    def __init__(self, paths: list[Path]):
        self._paths = paths

    def records(self) -> Iterator[RecordText]:
        for given in self._paths:
            files = sorted(p for p in given.rglob("*") if p.is_file()) if given.is_dir() else [given]
            for file in files:
                yield RecordText(file.as_posix(), as_text(file.name, file.read_bytes()))
