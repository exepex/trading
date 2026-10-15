"""Session exports shaped like the real `get_session` and `list_events(kinds=["result"])` output read on 15 Oct 2026
(field names copied; values made up). Each result event also carries a reply text, which must never reach a ledger."""

from __future__ import annotations

import json
from pathlib import Path

SESSION_ID = "session_01TESTxyz"
REPLY = "a reply text that must never reach the ledger"


def result_event(created_at: str, duration_ms: int, uuid: str, output_tokens: int | None = 100) -> dict:
    usage = None
    if output_tokens is not None:
        usage = {"input_tokens": 4, "output_tokens": output_tokens, "cache_read_input_tokens": 1000,
                 "cache_creation_input_tokens": 50, "service_tier": "standard"}  # fmt: skip
    catchall = {"duration_ms": duration_ms, "duration_api_ms": duration_ms * 2, "num_turns": 3, "result": REPLY,
                "session_id": "a360773c", "usage": usage, "total_cost_usd": 0.5}  # fmt: skip
    return {"created_at": created_at, "result": {"uuid": uuid, "internal_anthropic_catchall": catchall}}


def export(events: list[dict], has_more: bool = False, wrapped: bool = True) -> dict:
    session = {"id": SESSION_ID, "title": "Builder", "configured_model": "model-x", "session_context": {"model": "m"}}
    page = {"data": events, "has_more": has_more, "first_id": "a", "last_id": "b"}
    return {"session": {"ccr": session} if wrapped else session, "result_pages": [{"ccr": page} if wrapped else page]}


def write_export(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "export.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


TWO_DAYS = [
    result_event("2026-10-14T18:00:00Z", 60_000, "u1"),  # 23:30 IST on 14 Oct
    result_event("2026-10-14T18:40:00Z", 90_000, "u2"),  # 00:10 IST on 15 Oct
    result_event("2026-10-15T01:00:00Z", 30_000, "u3"),  # 06:30 IST on 15 Oct
]
