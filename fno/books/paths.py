"""Where a book's account lives, and the firewall that keeps every account object inside its own book (E1 criterion 6,
design 12.6: books never share money, positions or results)."""

from __future__ import annotations

from pathlib import Path

from ..constants import BOOKS, JOURNAL_FOLDER

ACCOUNT_FOLDER = "account"


class BookPathError(ValueError):
    """A book name that is not one of the three books, or a path that leaves the book's own account folder."""


def account_folder(root: Path, book: str) -> Path:
    """`<root>/journal/<book>/account` for one of the three books; anything else is refused."""
    if book not in BOOKS:
        raise BookPathError(f"unknown book {book!r}; the books are {', '.join(BOOKS)}")
    return Path(root) / JOURNAL_FOLDER / book / ACCOUNT_FOLDER


def file_in_account(folder: Path, name: str) -> Path:
    """A file directly inside the account folder. Refuses separators, `..` and any path that resolves (through a
    symbolic link, say) outside the folder, so no code path reaches another book's files through an account object."""
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        raise BookPathError(f"{name!r} is not a plain file name inside the account folder")
    path = folder / name
    if not path.resolve().is_relative_to(folder.resolve()) or not _folder_is_its_own(folder):
        raise BookPathError(f"{path} resolves outside its book's account folder {folder}")
    return path


def _folder_is_its_own(folder: Path) -> bool:
    """The account folder itself must not be a link into another book (journal/book1_rules/account -> book2's)."""
    resolved = folder.resolve()
    return resolved.name == folder.name and resolved.parent.name == folder.parent.name
