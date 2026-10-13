"""Firing the AI books (stories F1 and G5), run by the forecast-capture GitHub Actions job right after it committed
the day's v2 pack: one pointer per book to its own routine (O6's `/fire` trigger), Hybrid's with the rules' numbers,
the AI team's without. The fire log (`<d>_fired.json`, committed with the records after 15:15) keeps each routine's
session link for the audit. Fired once per day; every failure posts one #fno-desk line and is recorded, never retried
with more time. A book stopped by two transcript breaches (`stop_rule.py`) is not fired."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ..alerts.sender import AlertSender
from ..constants import AI_BOOKS, BOOK2_HYBRID
from ..pipeline.trigger import FireFailed, RoutineTrigger
from .paths import fired_path, pack_path
from .pointer import BookPointer
from .rules import RulesMissing, rules_of_day
from .stop_rule import stop_reason
from .versions import current_version

LINE = "Omenix F&O AI forecasts (GitHub Actions): {day}: {result}"


@dataclass
class AiBookFirer:
    root: Path
    triggers: dict[str, RoutineTrigger]  # book -> its routine's trigger
    alerts: AlertSender
    clock: Callable[[], datetime]

    def fire(self, day: date) -> list[str]:
        pack_file, log_file = self.root / pack_path(day), self.root / fired_path(day)
        if not pack_file.is_file():
            return [LINE.format(day=day, result="no v2 pack for the day; nothing fired")]
        if log_file.is_file():
            return [LINE.format(day=day, result="already fired (fired once per day)")]
        pack_sha = hashlib.sha256(pack_file.read_bytes()).hexdigest()
        log = {book: self._fire_one(day, book, pack_sha) for book in AI_BOOKS}
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text(json.dumps(log, sort_keys=True, indent=1) + "\n", encoding="utf-8")
        fired = [book for book, entry in log.items() if entry["fired"]]
        return [LINE.format(day=day, result=f"fired {', '.join(fired) or 'none'} of {', '.join(AI_BOOKS)}")]

    def _fire_one(self, day: date, book: str, pack_sha: str) -> dict:
        version = current_version(book).label
        entry = {"version": version, "fired_at": self.clock().isoformat()}
        stopped = stop_reason(self.root, book, version, day)
        if stopped:
            self.alerts.send(LINE.format(day=day, result=f"{book} not fired: {stopped}"))
            return entry | {"fired": False, "reason": stopped}
        try:
            rules = rules_of_day(self.root, day) if book == BOOK2_HYBRID else None
            session = self.triggers[book].fire(BookPointer(book, day, pack_sha, version, rules))
        except (FireFailed, RulesMissing) as failed:
            self.alerts.send(LINE.format(day=day, result=f"{book} not fired: {failed}; its day records no forecast"))
            return entry | {"fired": False, "reason": str(failed)}
        return entry | {"fired": True, "session": session}
