"""The announcements tables' rows (story A21 part 2): one item row per `seq_id` the first time a run sees it, and one
poll row per mark. An item missing `seq_id` or `exchdisstime` is refused, never guessed."""

from __future__ import annotations

from datetime import datetime

from .constants import ITEM_COLUMNS

FIELDS = {"seq_id": "seq_id", "symbol": "symbol", "isin": "sm_isin", "desc": "desc", "an_dt": "an_dt",
          "exchdisstime": "exchdisstime", "attachment_url": "attchmntFile"}  # fmt: skip
REQUIRED = ("seq_id", "exchdisstime")


class ItemRefused(ValueError):
    """An NSE item without a field the record needs."""


def item_row(item: dict, seen_at: datetime, run_id: str) -> dict:
    missing = [name for name in REQUIRED if not item.get(FIELDS[name])]
    if missing:
        raise ItemRefused(f"announcement without {missing[0]}")
    row = {name: str(item.get(source) or "") for name, source in FIELDS.items()}
    row.update(first_seen_at=seen_at.isoformat(), run_id=run_id)
    return {column: row[column] for column in ITEM_COLUMNS}


def poll_row(mark: datetime, requested_at: datetime, status: str, kind: str, items: int, new: int, run_id: str) -> dict:
    return {"mark": mark.isoformat(), "requested_at": requested_at.isoformat(), "status": status, "kind": kind,
            "items": str(items), "new_items": str(new), "run_id": run_id}  # fmt: skip
