"""What carries a number in a checkout (story O12): the series' files and the numbered addendum headings in them."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from fno.numbering.categories import AddendumCategory, Category

ADDENDUM_HEADING = re.compile(r"^## Addendum ([1-9]\d*)\b", re.MULTILINE)


@dataclass(frozen=True)
class NumberedItem:
    number: str
    name: str  # the file name; for an addendum, the file it is in
    where: str  # repository path, for the finding lines


def numbered_items(root: Path, category: Category) -> list[NumberedItem]:
    folder = root / category.folder
    files = sorted(p for p in folder.glob("*.md") if category.file_number(p.name)) if folder.is_dir() else []
    if isinstance(category, AddendumCategory):
        return [item for path in files for item in _addenda(root, category, path)]
    return [NumberedItem(category.file_number(p.name), p.name, p.relative_to(root).as_posix()) for p in files]


def _addenda(root: Path, category: AddendumCategory, path: Path) -> list[NumberedItem]:
    report = category.file_number(path.name)
    where = path.relative_to(root).as_posix()
    headings = ADDENDUM_HEADING.findall(path.read_text(encoding="utf-8"))
    return [NumberedItem(f"{report}.{k}", path.name, where) for k in headings]
