"""The decider's write paths as they were just before `decide()` (story F1t, agreed with F6): every file's bytes and
every folder. A refused or failed decision puts each path back exactly (changed files rewritten, new files and new
folders removed), so nothing half-written (a registry row, a spec file, a ledger row) can be committed later. The
snapshot, not `HEAD`, is the reference: `research/ledger.csv` is shared with the research factory, so a change made
before `decide()` by anyone is kept. The daily run is one thread, so nothing else writes these paths meanwhile."""

from __future__ import annotations

import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WriteSnapshot:
    root: Path
    paths: tuple[str, ...]
    files: dict[str, bytes]  # repository path -> bytes
    folders: frozenset[str]

    @classmethod
    def take(cls, root: Path, paths: Sequence[str]) -> WriteSnapshot:
        root = Path(root)
        files, folders = {}, set()
        for found in _under(root, paths):
            name = found.relative_to(root).as_posix()
            if found.is_dir():
                folders.add(name)
            else:
                files[name] = found.read_bytes()
        return cls(root, tuple(paths), files, frozenset(folders))

    def changed(self) -> list[str]:
        """Every path under the write paths that differs from the snapshot (new, changed or removed), sorted."""
        now = {p.relative_to(self.root).as_posix(): p for p in _under(self.root, self.paths) if p.is_file()}
        differing = {name for name, path in now.items() if self.files.get(name) != path.read_bytes()}
        return sorted(differing | (set(self.files) - set(now)))

    def restore(self) -> list[str]:
        """Puts every write path back to the snapshot; returns what it changed."""
        changed = self.changed()
        for name in changed:
            path = self.root / name
            if name in self.files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(self.files[name])
            else:
                path.unlink()
        new_folders = [p for p in _under(self.root, self.paths) if p.is_dir()]
        for folder in sorted(new_folders, key=lambda p: len(p.parts), reverse=True):
            if folder.relative_to(self.root).as_posix() not in self.folders and folder.exists():
                shutil.rmtree(folder)
        return changed


def _under(root: Path, paths: Sequence[str]) -> list[Path]:
    found = []
    for name in paths:
        target = root / name
        if target.is_file():
            found.append(target)
        elif target.is_dir():
            found += [target, *target.rglob("*")]
    return found


def is_under(root: Path, path: Path, paths: Sequence[str]) -> bool:
    """True when `path` is one of `paths` or inside one of them (no `..` or link can escape)."""
    resolved = Path(path).resolve()
    return any(resolved == (Path(root) / p).resolve() or resolved.is_relative_to((Path(root) / p).resolve())
               for p in paths)  # fmt: skip
