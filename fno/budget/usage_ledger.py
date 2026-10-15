"""The AI usage ledger `accounting/ai_usage.csv` (story F8): one row per AI session per IST day, written once and never
rewritten. Rows come only from a `SessionUsageReader`; only complete days (before today in IST) are recorded."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..constants import AI_BOOKS, PURPOSE_BOOKS_AND_ROLES, USAGE_PURPOSES
from .usage_export import TOKEN_FIELDS, DayUsage

LEDGER_FILE = "accounting/ai_usage.csv"
COLUMNS = ("date", "purpose", "book", "role_or_bundle", "session_id", "model", "minutes", "turns",
           *TOKEN_FIELDS, "tokens_basis", "source")  # fmt: skip
TOKENS_BASIS = "main-loop usage of result events (side calls not included)"
SOURCE = "get_session + list_events(result) export"
NOT_COMPLETE = "{day} is not a complete day yet (today in IST is {today}): record it tomorrow"


class UsageRefused(ValueError):
    """The row cannot be recorded; the message says why."""


@dataclass(frozen=True)
class Attribution:
    """Who the session worked for: books and roles (counts against the cap) or development."""

    purpose: str
    book: str = ""  # an AI book for a book's session, else empty
    role_or_bundle: str = ""

    def check(self) -> None:
        if self.purpose not in USAGE_PURPOSES:
            raise UsageRefused(f"purpose must be one of {USAGE_PURPOSES}, not {self.purpose!r}")
        if self.book and self.book not in AI_BOOKS:
            raise UsageRefused(f"book must be one of {AI_BOOKS} or empty, not {self.book!r}")
        if self.book and self.purpose != PURPOSE_BOOKS_AND_ROLES:
            raise UsageRefused("a book's session is books_and_roles use")
        if not (self.book or self.role_or_bundle):
            raise UsageRefused("name the book or the role (or bundle) the session worked for")


class UsageLedger:
    def __init__(self, root: Path):
        self._path = root / LEDGER_FILE

    def rows(self) -> list[dict]:
        if not self._path.is_file():
            return []
        reader = csv.DictReader(io.StringIO(self._path.read_text(encoding="utf-8")))
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError(f"{LEDGER_FILE} columns must be {COLUMNS}")
        return list(reader)

    def record(self, days: list[DayUsage], who: Attribution, today: date) -> list[str]:
        """Appends the complete days not recorded yet; returns one line per day (recorded or why not)."""
        who.check()
        known = {(row["session_id"], row["date"]) for row in self.rows()}
        lines, new = [], []
        for usage in days:
            key = (usage.session_id, usage.day.isoformat())
            if usage.day >= today:
                lines.append(NOT_COMPLETE.format(day=usage.day, today=today))
            elif key in known:
                lines.append(f"{usage.day} {usage.session_id}: already recorded (never rewritten)")
            else:
                new.append(_row(usage, who))
                lines.append(f"{usage.day} {usage.session_id}: recorded {usage.minutes} minutes, {usage.turns} turns")
        if new:
            self._append(new)
        return lines

    def _append(self, rows: list[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fresh = not self._path.is_file()
        with self._path.open("a", encoding="utf-8", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
            if fresh:
                writer.writeheader()
            writer.writerows(rows)


def _row(usage: DayUsage, who: Attribution) -> dict:
    tokens = usage.tokens or {}
    row = {"date": usage.day.isoformat(), "purpose": who.purpose, "book": who.book,
           "role_or_bundle": who.role_or_bundle, "session_id": usage.session_id, "model": usage.model,
           "minutes": f"{usage.minutes:.2f}", "turns": usage.turns}  # fmt: skip
    row |= {column: tokens.get(column, "") for column in TOKEN_FIELDS}  # blank: unknown, never zero
    return row | {"tokens_basis": TOKENS_BASIS if usage.tokens else "not available", "source": SOURCE}
