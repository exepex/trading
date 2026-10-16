"""The number check (story O12): every numbered file or heading has its registry row, and no number is used twice.

Seeded history (session `existing`) may hold a number twice; nothing claimed after the seed may. Seeded rows come
first in each registry, so the seed cannot be reused later to register a clash.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from fno.numbering.categories import CATEGORIES, Category
from fno.numbering.numbered_items import NumberedItem, numbered_items
from fno.numbering.registry import Row, read_rows, valid_stamp

NO_ROW = "{where}: number {number} has no row in {registry}"
SHARED = "{registry}: number {number} is used {count} times ({names}); only seeded history may repeat a number"
BAD_ROW = "{registry}: row {number},{name}: {reason}"
SEED_AFTER_CLAIM = "{registry}: seeded row {number} comes after a claimed row; the seed is history only"


def check_numbers(root: Path) -> list[str]:
    """One finding line per problem, across every category; empty when clean."""
    return [line for category in CATEGORIES.values() for line in _check_category(root, category)]


def _check_category(root: Path, category: Category) -> list[str]:
    try:
        rows = read_rows(root / category.registry)
    except ValueError as malformed:
        return [f"{category.registry}: {malformed}"]
    items = numbered_items(root, category)
    return [
        *_bad_rows(category, rows),
        *_missing_rows(category, rows, items),
        *_shared_numbers(category, rows, items),
    ]


def _bad_rows(category: Category, rows: list[Row]) -> list[str]:
    found, claimed_seen = [], False
    for row in rows:
        reason = _row_problem(category, row)
        if reason:
            found.append(BAD_ROW.format(registry=category.registry, number=row.number, name=row.name, reason=reason))
        if row.seeded and claimed_seen:
            found.append(SEED_AFTER_CLAIM.format(registry=category.registry, number=row.number))
        claimed_seen = claimed_seen or not row.seeded
    return found


def _row_problem(category: Category, row: Row) -> str | None:
    if not category.valid_number(row.number):
        return "number is not of this category's form"
    if not row.name:
        return "no name"
    if row.seeded:
        return "a seeded row has no time" if row.claimed_at_utc else None
    if not row.session:
        return "no claiming session"
    return None if valid_stamp(row.claimed_at_utc) else "claimed_at_utc is not YYYY-MM-DDTHH:MM:SSZ"


def _missing_rows(category: Category, rows: list[Row], items: list[NumberedItem]) -> list[str]:
    registered = {category.key(row.number, row.name) for row in rows}
    missing = [item for item in items if category.key(item.number, item.name) not in registered]
    return [NO_ROW.format(where=i.where, number=i.number, registry=category.registry) for i in missing]


def _shared_numbers(category: Category, rows: list[Row], items: list[NumberedItem]) -> list[str]:
    """A number held by two rows, or by more files or headings than it has seeded rows."""
    row_count = Counter(row.number for row in rows)
    seeded_count = Counter(row.number for row in rows if row.seeded)
    item_count = Counter(item.number for item in items)
    found = []
    for number in sorted(set(row_count) | set(item_count), key=_order):
        uses = max(row_count[number], item_count[number])
        if uses > 1 and seeded_count[number] < uses:
            names = sorted({row.name for row in rows if row.number == number} | _item_names(items, number))
            found.append(SHARED.format(registry=category.registry, number=number, count=uses, names=", ".join(names)))
    return found


def _item_names(items: list[NumberedItem], number: str) -> set[str]:
    return {item.name for item in items if item.number == number}


def _order(number: str) -> tuple[int, ...]:
    return tuple(int(part) if part.isdigit() else 0 for part in number.split("."))
