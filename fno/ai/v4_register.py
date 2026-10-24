"""Story G11 C13, the AI books' 10 slot registrations (`hybrid` and `ai_team` on each of the five family questions),
appended to `research/forecasts/v4_slots.csv` in the protocol's order:

1. `FREEZE_v4.md` and the rules rows exist (the freeze builder's; owner, 21 Oct 2026, "v4 freeze answers" (3));
2. these rows, each `effective_start` = the first scored session after the freeze's day, never after any slot's first
   eligible session (`slot_file.py` refuses a later start for the whole file, which would stop every v4 score), with
   `registered_on` = the day written, before that session opens (09:15 IST);
3. `daily.live_from.ai_books_v4` set by the owner to that same session; a later go-live leaves `not_fired` misses.

Refused, writing nothing: before the freeze, without every rules row, once the first session has begun, a file that
already holds a different AI row, or a result `SlotFile` itself refuses. `--print` gives the rows for the freeze commit
instead of writing them, the safe way to land them on the freeze's own day."""

from __future__ import annotations

import csv
import io
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

from ..constants import AI_BOOKS, FORECAST_PROTOCOL_V4, V4_SLOT_RULES
from ..forecast_scoring.v4.records import LookRecords, SlotRegistry
from ..forecast_scoring.v4.slot_file import COLUMNS, RegistrationRefused
from ..forecast_v4.terms import FAMILY_QUESTIONS
from ..models import IST
from .v4_rows import SLOTS
from .versions import current_version

DECISION = "DESK_DECISIONS 21 Oct 2026 v4 freeze answers (3); 24 Oct 2026 Close v4 in full first"
SESSION_OPENS = time(9, 15)
LINE = "Omenix F&O AI v4 slots: {result}"
LOOK_AHEAD_DAYS = 15  # the first scored session after the freeze is found within this many calendar days


class RegisterRefused(ValueError):
    """The registration would break the protocol's order or the slot file; nothing is written."""


@dataclass
class SlotRegistrar:
    slots_file: Path
    looks: LookRecords
    slots: Callable[[], SlotRegistry]  # G8's reading of `slots_file` (its own freeze and eligibility checks)
    sessions: Callable[[date, date], list[date]]  # v4's scored sessions from the first day to the last
    clock: Callable[[], datetime]

    def rows(self) -> list[dict]:
        """The 10 rows, once every check before writing passes."""
        if not self.looks.frozen():
            raise RegisterRefused("FREEZE_v4.md does not exist: the AI slots are registered after the freeze")
        registered = self.slots().registered()
        missing = [q for q in FAMILY_QUESTIONS if (q, V4_SLOT_RULES) not in registered]
        if missing:
            raise RegisterRefused(f"no rules row for {', '.join(missing)}: the freeze's rules rows come first")
        start = self._first_session_after(self.looks.frozen_on())
        now = self.clock().astimezone(IST)
        if now >= datetime.combine(start, SESSION_OPENS, IST):
            raise RegisterRefused(f"the slots' first session {start} has begun: a row must be written before it")
        forecaster = {book: current_version(book, FORECAST_PROTOCOL_V4).forecaster for book in AI_BOOKS}
        return [{"question": q, "slot": SLOTS[book], "forecaster": forecaster[book], "effective_start": f"{start}",
                 "registered_on": now.date().isoformat(), "decision": DECISION}
                for q in FAMILY_QUESTIONS for book in AI_BOOKS]  # fmt: skip

    def register(self, write: bool) -> list[str]:
        try:
            rows = self.rows()
            return self._append(rows) if write else [_text(rows, header=False).rstrip("\n")]
        except (RegisterRefused, RegistrationRefused) as refused:
            return [LINE.format(result=f"refused, nothing written: {refused}")]

    def _append(self, rows: list[dict]) -> list[str]:
        existing = self.slots().registered()
        wanted = {(r["question"], r["slot"]): r["forecaster"] for r in rows}
        present = {k: v.forecaster for k, v in existing.items() if k in wanted}
        if present == wanted:
            return [LINE.format(result=f"already registered ({len(wanted)} rows)")]
        if present:
            raise RegisterRefused("the slot file already holds another AI registration (the first one is the member)")
        before = self.slots_file.read_text(encoding="utf-8") if self.slots_file.is_file() else ""
        self.slots_file.write_text(before + _text(rows, header=not before), encoding="utf-8")
        try:
            self.slots().registered()  # G8's own reading of the result
        except RegistrationRefused:
            self._restore(before)
            raise
        start = rows[0]["effective_start"]
        return [LINE.format(result=f"{len(rows)} rows registered, effective {start}: {self.slots_file.name}")]

    def _restore(self, before: str) -> None:
        if before:
            self.slots_file.write_text(before, encoding="utf-8")
        else:
            self.slots_file.unlink()

    def _first_session_after(self, day: date) -> date:
        found = self.sessions(day + timedelta(days=1), day + timedelta(days=LOOK_AHEAD_DAYS))
        if not found:
            raise RegisterRefused(f"no scored session within {LOOK_AHEAD_DAYS} days after {day}")
        return found[0]


def _text(rows: list[dict], header: bool) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
    if header:
        writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()
