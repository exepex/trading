"""The open run of each routine on this machine, kept in a git-ignored file between the routine's commands (each
`Bash` call of a routine session is a new shell, so nothing can live in memory). Two steps can run at once (the
pre-open's background part), so every read-change-write of a routine's file holds that routine's lock."""

from __future__ import annotations

import contextlib
import fcntl
import json
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from .layout import RunFolder


@dataclass
class OpenRun:
    folder: RunFolder
    steps: int = 0
    failed: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        data = asdict(self)
        data["folder"]["day"] = self.folder.day.isoformat()
        return json.dumps(data)

    @classmethod
    def from_json(cls, text: str) -> OpenRun:
        data = json.loads(text)
        folder = data["folder"]
        return cls(RunFolder(date.fromisoformat(folder["day"]), folder["routine"], folder["run"]),
                   data["steps"], data["failed"])  # fmt: skip


class RunStateFolder:
    def __init__(self, folder: Path):
        self.folder = folder

    def _file(self, routine: str) -> Path:
        return self.folder / f"{routine}.json"

    def load(self, routine: str) -> OpenRun | None:
        path = self._file(routine)
        return OpenRun.from_json(path.read_text(encoding="utf-8")) if path.exists() else None

    def save(self, run: OpenRun) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        self._file(run.folder.routine).write_text(run.to_json(), encoding="utf-8")

    @contextlib.contextmanager
    def locked(self, routine: str) -> Iterator[None]:
        self.folder.mkdir(parents=True, exist_ok=True)
        with open(self.folder / f"{routine}.lock", "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def clear(self, routine: str) -> None:
        self._file(routine).unlink(missing_ok=True)
