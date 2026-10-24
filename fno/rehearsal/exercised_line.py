"""The rehearsal's one line on what it exercised (story REH1j): every step and quote part not live in real runs on the
replayed day, in the order the steps ran, with what it did. It is printed after the daily run's last line and posted
once to #fno-desk (labelled, as every rehearsal post is), so the owner sees an exercised failure or a command not
built yet, warned and never hidden (owner, 24 Oct: DESK_DECISIONS "The card warns when any step failed" and "Pilot
mode ... Publish to slack"), while the day's own last line keeps the real day's rule. Read from the run's private full
log (`journal/runs/.full/<day>.json`), which keeps the reasons the committed log keeps only as codes."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date
from pathlib import Path

from ..alerts.sender import AlertSender
from ..constants import EXERCISED_PARTS, STEP_EXERCISED, STEP_FAILED, STEP_NOT_BUILT, STEP_NOT_LIVE, STEP_OK
from ..daily.full_log import FULL_LOGS

EXERCISED_LINE = "not live in real runs (exercised): {items}"
PART = "{step}'s {part} part"


def exercised_line(steps: dict[str, dict]) -> str | None:
    """The line for a run log's steps, or None when nothing was exercised."""
    items = []
    for name, step in steps.items():
        result = step["result"]
        if result.get("status") == STEP_NOT_LIVE and STEP_EXERCISED in result:
            items.append(_item(name, result[STEP_EXERCISED]))
        parts = result.get(EXERCISED_PARTS, {})
        items += [_item(PART.format(step=name, part=part), done) for part, done in parts.items()]
    return EXERCISED_LINE.format(items="; ".join(items)) if items else None


def _item(what: str, done: dict) -> str:
    status = done.get("status")
    if status == STEP_NOT_BUILT:
        return f"{what} not built"
    reason = done.get("reason")
    return f"{what} {status}: {reason}" if status != STEP_OK and reason else f"{what} {status}"


def not_live_result(code: int, last: str) -> dict:
    """A rehearsed routine's command not live in real runs (REH1k), in the run log's shape: its exit and last line."""
    done = {"status": STEP_OK} if code == 0 else {"status": STEP_FAILED, "reason": last or f"exit {code}"}
    return {"status": STEP_NOT_LIVE, STEP_EXERCISED: done}


def report_exercised(checkout: Path, day: date, out: Callable[[str], None], alerts: AlertSender,
                     commands: dict[str, dict] | None = None) -> None:  # fmt: skip
    """Prints and posts the line once, when the rehearsal exercised anything: the daily run's steps (its full log)
    and the routine's own commands not live in real runs (`commands`, REH1k)."""
    path = Path(checkout) / FULL_LOGS / f"{day.isoformat()}.json"
    steps = json.loads(path.read_text(encoding="utf-8"))["steps"] if path.is_file() else {}
    line = exercised_line({**steps, **(commands or {})})
    if line is not None:
        out(line)
        alerts.send(line)
