"""Reading one AI session's usage (story F8). Python cannot call Claude's session tools, so a Claude session saves them
into one JSON file outside the repository: `{"session": <get_session>, "result_pages": [<list_events(kinds=["result"])
page>, ...]}`, every page back to the oldest. `SessionUsageReader` is the interface; `ExportFileUsageReader` reads
such a file. Only numbers are taken, never message text: per IST day, the wall minutes of that day's turns
(`duration_ms`) and their main-loop tokens (`usage`), blank when any turn of the day lacks them."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ..models import IST

TOKEN_FIELDS = {  # ledger column -> field of a result event's `usage`
    "input_tokens": "input_tokens",
    "output_tokens": "output_tokens",
    "cache_read_tokens": "cache_read_input_tokens",
    "cache_write_tokens": "cache_creation_input_tokens",
}
INCOMPLETE = "the export has no page with has_more false: older result events are missing, so nothing is recorded"
NO_SESSION_ID = "the export's session record has no id"


class ExportRefused(ValueError):
    """The export cannot be read without guessing; the message says why."""


@dataclass(frozen=True)
class DayUsage:
    day: date
    session_id: str
    model: str
    minutes: float
    turns: int
    tokens: dict[str, int] | None  # None: at least one turn of the day carried no usage, so tokens are unknown


class SessionUsageReader(ABC):
    @abstractmethod
    def days(self) -> list[DayUsage]:
        """One usage line per IST day on which the session had a finished turn, oldest first."""


class ExportFileUsageReader(SessionUsageReader):
    def __init__(self, path: Path):
        self._export = json.loads(path.read_text(encoding="utf-8"))

    def days(self) -> list[DayUsage]:
        session = _unwrap(self._export.get("session") or {})
        session_id = session.get("id") or ""
        if not session_id:
            raise ExportRefused(NO_SESSION_ID)
        model = session.get("configured_model") or (session.get("session_context") or {}).get("model") or ""
        by_day = defaultdict(list)
        for result in _results(self._export.get("result_pages") or []):
            by_day[_ist_day(result["created_at"])].append(result["result"])
        return [_day_usage(day, session_id, model, by_day[day]) for day in sorted(by_day)]


def _unwrap(part: dict) -> dict:
    return part.get("ccr", part)


def _results(pages: list) -> list[dict]:
    pages = [_unwrap(page) for page in pages]
    if not any(page.get("has_more") is False for page in pages):
        raise ExportRefused(INCOMPLETE)
    seen, results = set(), []
    for page in pages:
        for event in page.get("data") or []:
            result = event.get("result")
            uuid = (result or {}).get("uuid")
            if result is None or (uuid and uuid in seen):
                continue  # another kind of event, or the same event on two pages
            seen.add(uuid)
            results.append({"created_at": event["created_at"], "result": _figures(result)})
    return results


def _figures(result: dict) -> dict:
    """The few numbers of a result event; its text (the reply) is dropped here."""
    figures = result.get("internal_anthropic_catchall", result)
    return {"duration_ms": figures.get("duration_ms"), "usage": figures.get("usage")}


def _ist_day(created_at: str) -> date:
    return datetime.fromisoformat(created_at.replace("Z", "+00:00")).astimezone(IST).date()


def _day_usage(day: date, session_id: str, model: str, turns: list[dict]) -> DayUsage:
    if any(not isinstance(turn["duration_ms"], int | float) for turn in turns):
        raise ExportRefused(f"{day}: a result event has no duration_ms")
    minutes = round(sum(turn["duration_ms"] for turn in turns) / 60000, 2)
    return DayUsage(day, session_id, model, minutes, len(turns), _tokens(turns))


def _tokens(turns: list[dict]) -> dict[str, int] | None:
    usages = [turn["usage"] for turn in turns]
    if any(
        not isinstance(u, dict) or any(not isinstance(u.get(f), int) for f in TOKEN_FIELDS.values()) for u in usages
    ):
        return None
    return {column: sum(u[field] for u in usages) for column, field in TOKEN_FIELDS.items()}
