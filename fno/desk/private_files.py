"""The private paper records in Drive (story E2c): each account's files (E1's ledger, equity history and positions,
E4's desk records) and each book's private packs live in Drive's `paper` area, under their repository paths, and are
mirrored in git-ignored local folders. A reader pulls them before it reads; a writer pushes what it wrote. Nothing here
is committed: the public record keeps per-book daily totals only (owner, 15 Oct 2026, "A: move to Drive")."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from ..books.account import EQUITY_HISTORY_FILE, POSITIONS_FILE
from ..books.paths import account_folder, shadow_account
from ..constants import BOOKS, CASH_LEDGER_FILE, JOURNAL_FOLDER, SHADOW_FOLDER
from ..storage.index_store import IndexFileStore
from .daily_ports import CommitFailed
from .records import EVENTS_FILE, FILLS_FILE

ACCOUNT_FILES = (CASH_LEDGER_FILE, EQUITY_HISTORY_FILE, POSITIONS_FILE, FILLS_FILE, EVENTS_FILE)
UNAVAILABLE = "the private paper records in Drive could not be {what} ({path}: {why})"


class PrivateFilesUnavailable(CommitFailed):
    """Drive could not be read or written. For E3's daily run it is a failed commit: the one handler alerts and stops
    the run, nothing is committed for the step, and the rerun repeats it."""


def paper_accounts(root: Path) -> list[str]:
    """The three books and every shadow account the repository names (its folder under `journal/shadow/`)."""
    shadow = Path(root) / JOURNAL_FOLDER / SHADOW_FOLDER
    versions = sorted(p.name for p in shadow.iterdir() if p.is_dir()) if shadow.is_dir() else []
    return [*BOOKS, *(shadow_account(v) for v in versions)]


def account_paths(root: Path, account: str) -> list[Path]:
    folder = account_folder(root, account)
    return [folder / name for name in ACCOUNT_FILES]


class PrivateFiles:
    def __init__(self, store: Callable[[], IndexFileStore], root: Path):
        self._store, self._opened, self.root = store, None, Path(root)  # opened at the first pull or push

    def pull_accounts(self) -> None:
        """The one shared download at the start of a run or command that reads accounts (story E2c)."""
        self.pull(p for account in paper_accounts(self.root) for p in account_paths(self.root, account))

    def pull_account(self, account: str) -> None:
        self.pull(account_paths(self.root, account))

    def push_account(self, account: str) -> None:
        self.push(account_paths(self.root, account))

    def pull(self, paths: Iterable[Path]) -> None:
        """Each file as Drive holds it; a file Drive does not hold yet is left as it is locally."""
        for path in paths:
            data = self._call("read", path, lambda name: self.store().get(name))
            if data is not None:
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_name(f".{path.name}.pull")
                temporary.write_bytes(data)
                temporary.replace(path)

    def push(self, paths: Iterable[Path]) -> None:
        """Each local file to Drive, replacing the previous version; a file not written locally is skipped."""
        for path in paths:
            if path.is_file():
                data = path.read_bytes()
                self._call("written", path, lambda name, data=data: self.store().replace(name, data))

    def store(self) -> IndexFileStore:
        if self._opened is None:
            self._opened = self._store()
        return self._opened

    def _call(self, what: str, path: Path, action):
        name = Path(path).relative_to(self.root).as_posix()
        try:
            return action(name)
        except Exception as problem:  # noqa: BLE001 - any Drive failure stops the step that needed it, named
            raise PrivateFilesUnavailable(UNAVAILABLE.format(what=what, path=name, why=problem)) from problem
