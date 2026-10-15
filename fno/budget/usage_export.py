"""Reading one AI session's usage (story F8). Python cannot call Claude's session tools, so a Claude session saves them
into one JSON file outside the repository: `{"captured_at": <ISO time with zone>, "session": <get_session>,
"result_pages": [{"before_id": <cursor used, null for the first call>, "response": <list_events(kinds=["result"])>},
...]}`, newest page first, back to the oldest. `SessionUsageReader` is the interface; `ExportFileUsageReader` reads
such a file. The pages must chain (each cursor is the newer page's `first_id`; only the last has `has_more` false), so a
dropped page is refused. Only numbers are taken, never message text: per IST day, the wall minutes of that day's turns
(`duration_ms`) and their main-loop tokens (`usage`), blank when any turn of the day lacks them. Days on or after the
capture's IST date are not complete in the export, so they are never recorded from it."""

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
INCOMPLETE = "the export's last page has has_more true: older result events are missing, so nothing is recorded"
BROKEN_CHAIN = "page {n} was not read with the previous page's first_id: a page is missing, so nothing is recorded"
MORE_AFTER_END = "page {n} has has_more false but more pages follow: the pages are out of order"
NO_SESSION_ID = "the export's session record has no id"
NO_RESULTS = "the export holds no result events: nothing to record (a changed export shape is refused, not skipped)"
NO_ZONE = "{what} {value!r} has no time zone"


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

    @abstractmethod
    def captured_on(self) -> date:
        """The IST day the usage was read: that day and later ones are not complete in this reading."""


class ExportFileUsageReader(SessionUsageReader):
    def __init__(self, path: Path):
        self._export = json.loads(path.read_text(encoding="utf-8"))

    def captured_on(self) -> date:
        return _ist(self._export.get("captured_at") or "", "captured_at").date()

    def days(self) -> list[DayUsage]:
        session = _unwrap(self._export.get("session") or {})
        session_id = session.get("id") or ""
        if not session_id:
            raise ExportRefused(NO_SESSION_ID)
        model = session.get("configured_model") or (session.get("session_context") or {}).get("model") or ""
        by_day = defaultdict(list)
        for result in _results(self._export.get("result_pages") or []):
            by_day[_ist(result["created_at"], "created_at").date()].append(result["result"])
        return [_day_usage(day, session_id, model, by_day[day]) for day in sorted(by_day)]


def _unwrap(part: dict) -> dict:
    return part.get("ccr", part)


def _chained(pages: list) -> list[dict]:
    """The responses, once each page is shown to be read with the newer page's first_id and the last is the end."""
    responses, cursor = [], None
    for n, page in enumerate(pages, start=1):
        response = _unwrap(page.get("response") or {})
        if page.get("before_id") != cursor:
            raise ExportRefused(BROKEN_CHAIN.format(n=n))
        if responses and responses[-1].get("has_more") is False:
            raise ExportRefused(MORE_AFTER_END.format(n=n))
        responses.append(response)
        cursor = response.get("first_id")
    if not responses or responses[-1].get("has_more") is not False:
        raise ExportRefused(INCOMPLETE)
    return responses


def _results(pages: list) -> list[dict]:
    seen, results = set(), []
    for page in _chained(pages):
        for event in page.get("data") or []:
            result = event.get("result")
            if result is None:
                continue  # another kind of event
            uuid = result.get("uuid")
            if not uuid:
                raise ExportRefused(f"a result event of {event.get('created_at')} has no uuid")
            if uuid not in seen:
                seen.add(uuid)
                results.append({"created_at": event["created_at"], "result": _figures(result)})
    if not results:
        raise ExportRefused(NO_RESULTS)
    return results


def _figures(result: dict) -> dict:
    """The few numbers of a result event; its text (the reply) is dropped here."""
    figures = result.get("internal_anthropic_catchall", result)
    return {"duration_ms": figures.get("duration_ms"), "usage": figures.get("usage")}


def _ist(value: str, what: str) -> datetime:
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ExportRefused(f"{what} {value!r} is not an ISO time") from None
    if moment.tzinfo is None:
        raise ExportRefused(NO_ZONE.format(what=what, value=value))
    return moment.astimezone(IST)


def _day_usage(day: date, session_id: str, model: str, turns: list[dict]) -> DayUsage:
    if not all(_is_duration(turn["duration_ms"]) for turn in turns):
        raise ExportRefused(f"{day}: a result event has no valid duration_ms (a number of 0 or more)")
    minutes = round(sum(turn["duration_ms"] for turn in turns) / 60000, 2)
    return DayUsage(day, session_id, model, minutes, len(turns), _tokens(turns))


def _is_duration(value) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and value >= 0


def _tokens(turns: list[dict]) -> dict[str, int] | None:
    usages = [turn["usage"] for turn in turns]
    if any(not isinstance(u, dict) or any(not _is_count(u.get(f)) for f in TOKEN_FIELDS.values()) for u in usages):
        return None
    return {column: sum(u[field] for u in usages) for column, field in TOKEN_FIELDS.items()}


def _is_count(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
