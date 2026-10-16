"""The monitor's heartbeat and "monitor silent" (story LM1, design 6.5): after every mark it handles, the monitor
writes its latest mark row as `research/data/intraday/monitor/heartbeat.json`, through A16's `Heartbeat`. The silence
check reuses A16's rule (`heartbeat_state`: 30 minutes, 09:45-15:45 on a recorded session), never a copy, and speaks
only while positions are open: a monitor with nothing to watch is never "silent"."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..intraday.document import parse_time, utc_text
from ..intraday.heartbeat import SILENT, Heartbeat, heartbeat_state
from ..models import IST
from .mark_rows import MarkRow

MONITOR = "position-monitor"
SILENT_TEXT = (
    "Action: check the position monitor's routine (story LM1). WARNING, monitor silent: no monitor heartbeat for "
    "{minutes} minutes while {positions} positions are open; alert_only strategies continue and no exit changes."
)


@dataclass(frozen=True)
class SilenceResult:
    silent: bool
    minutes: int | None  # since the monitor last finished a mark; None when no heartbeat is readable
    positions: int
    line: str


class MonitorHeartbeat:
    def __init__(self, heartbeat: Heartbeat):
        self.heartbeat = heartbeat

    def beat(self, row: MarkRow) -> None:
        self.heartbeat.write({**row.as_csv(), "monitor": MONITOR, "run_finished_at": utc_text(row.finished_at)})


class MonitorSilence:
    def __init__(self, heartbeat, recorded_session):
        """`heartbeat`: anything with `read()` (A16's `Heartbeat`, or `PublishedHeartbeat` for GitHub's copy);
        `recorded_session(day)`: whether A16 records that day."""
        self.heartbeat, self.recorded_session = heartbeat, recorded_session

    def check(self, now: datetime) -> SilenceResult:
        beat = self.heartbeat.read() or {}
        positions = _positions(beat)
        state = heartbeat_state(beat or None, now, self.recorded_session(now.astimezone(IST).date()))
        minutes = _minutes(beat, now)
        if state.status != SILENT or not positions:
            return SilenceResult(False, minutes, positions, state.line)
        text = SILENT_TEXT.format(minutes="?" if minutes is None else minutes, positions=positions)
        return SilenceResult(True, minutes, positions, text)


def _positions(beat: dict) -> int:
    try:
        return int(beat.get("positions", 0))
    except (TypeError, ValueError):
        return 0


def _minutes(beat: dict, now: datetime) -> int | None:
    try:
        finished = parse_time(str(beat.get("run_finished_at", "")))
    except ValueError:
        return None
    return None if finished is None else int((now - finished).total_seconds() // 60)
