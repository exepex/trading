"""Session exports shaped like the real `get_session` and `list_events(kinds=["result"])` output read on 15 Oct 2026
(field names copied; values made up). Each result event also carries a reply text, which must never reach a ledger."""

from __future__ import annotations

import json
from pathlib import Path

SESSION_ID = "session_01TESTxyz"
REPLY = "a reply text that must never reach the ledger"
CAPTURED = "2026-10-16T09:00:00+05:30"  # the export was read on 16 Oct IST


def result_event(created_at: str, duration_ms: int, uuid: str, output_tokens: int | None = 100) -> dict:
    usage = None
    if output_tokens is not None:
        usage = {"input_tokens": 4, "output_tokens": output_tokens, "cache_read_input_tokens": 1000,
                 "cache_creation_input_tokens": 50, "service_tier": "standard"}  # fmt: skip
    catchall = {"duration_ms": duration_ms, "duration_api_ms": duration_ms * 2, "num_turns": 3, "result": REPLY,
                "session_id": "a360773c", "usage": usage, "total_cost_usd": 0.5}  # fmt: skip
    return {"created_at": created_at, "result": {"uuid": uuid, "internal_anthropic_catchall": catchall}}


def page(events: list[dict], has_more: bool, first_id: str, wrapped: bool = True) -> dict:
    response = {"data": events, "has_more": has_more, "first_id": first_id, "last_id": "x"}
    return {"ccr": response} if wrapped else response


def export(events: list[dict], has_more: bool = False, wrapped: bool = True, captured_at: str = CAPTURED) -> dict:
    """One page, or the events split over chained pages when `pages` is used instead."""
    session = {"id": SESSION_ID, "title": "Builder", "configured_model": "model-x", "session_context": {"model": "m"}}
    first = {"before_id": None, "response": page(events, has_more, "p1", wrapped)}
    return {"captured_at": captured_at, "session": {"ccr": session} if wrapped else session, "result_pages": [first]}


def chained(*event_pages: list[dict]) -> dict:
    """An export whose pages run newest to oldest, each read with the newer page's first_id."""
    data = export([])
    pages, cursor = [], None
    for n, events in enumerate(event_pages, start=1):
        last = n == len(event_pages)
        pages.append({"before_id": cursor, "response": page(events, not last, f"p{n}")})
        cursor = f"p{n}"
    return data | {"result_pages": pages}


def write_export(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "export.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


TWO_DAYS = [
    result_event("2026-10-14T18:00:00Z", 60_000, "u1"),  # 23:30 IST on 14 Oct
    result_event("2026-10-14T18:40:00Z", 90_000, "u2"),  # 00:10 IST on 15 Oct
    result_event("2026-10-15T01:00:00Z", 30_000, "u3"),  # 06:30 IST on 15 Oct
]
