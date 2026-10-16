"""The registry seed (story O12): one `existing` row for each numbered file or heading not registered yet.

Used when O12 merges, so the files already on `main` are history and not clashes. Once a category holds a claimed
row, the check refuses any seeded row after it, so the seed cannot register a new clash later.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from fno.numbering.categories import CATEGORIES
from fno.numbering.numbered_items import numbered_items
from fno.numbering.registry import SEEDED, Row, append_row, read_rows


def seed_registries(root: Path) -> int:
    """Appends the missing seeded rows to every registry; returns how many were added."""
    added = 0
    for category in CATEGORIES.values():
        path = root / category.registry
        registered = Counter(category.key(row.number, row.name) for row in read_rows(path))
        for item in numbered_items(root, category):
            key = category.key(item.number, item.name)
            if registered[key]:
                registered[key] -= 1
                continue
            append_row(path, Row(item.number, item.name, SEEDED))
            added += 1
    return added
