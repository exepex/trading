"""A routine's own timing of its run (owner's "5 A" of 15 Oct 2026: the routine records its own usage at the end of
each run). A routine cannot read its own `result` event before its turn ends, and a fired routine runs one turn, so at
its end the session tools show none of that run's usage. What it can record is its own wall time: it notes the time when
it starts and when it ends, with its session id from `get_session` (no id: the calling session), in a JSON file
`{"session_id", "model", "started_at", "ended_at"}`. Tokens are unknown. The run is over when the file is written, so
its day is complete for this session."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from .usage_reader import DayUsage, ExportRefused, SessionUsageReader, ist_time, shaped

SOURCE = "self-timed by the routine (start to end of its run)"
MAX_RUN = timedelta(hours=24)  # longer is a typo, not a run: refused, never recorded
LATER_THAN_TODAY = "ended_at {day} is after today ({today}): a run cannot end in the future"
BACKWARDS = "ended_at {end} is before started_at {start}"


class SelfTimedUsageReader(SessionUsageReader):
    def __init__(self, path: Path):
        self._record = shaped(json.loads(path.read_text(encoding="utf-8")), dict, "the timing record")

    def days(self) -> list[DayUsage]:
        start = ist_time(self._record.get("started_at") or "", "started_at")
        end = ist_time(self._record.get("ended_at") or "", "ended_at")
        if end < start:
            raise ExportRefused(BACKWARDS.format(end=end.isoformat(), start=start.isoformat()))
        if end - start > MAX_RUN:
            raise ExportRefused(f"the run lasted {end - start}, more than {MAX_RUN}: check started_at and ended_at")
        minutes = round((end - start).total_seconds() / 60, 2)
        session_id = self._record.get("session_id") or ""
        if not session_id:
            raise ExportRefused("the timing record has no session_id")
        # a run that crosses midnight IST counts on the day it ended
        model = self._record.get("model") or ""
        return [DayUsage(end.date(), session_id, model, minutes, 1, None, SOURCE)]

    def complete_before(self, today: date) -> date:
        day = self.days()[0].day
        if day > today:
            raise ExportRefused(LATER_THAN_TODAY.format(day=day, today=today))
        return day + timedelta(days=1)
