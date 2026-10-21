"""`python -m fno quotes record-indices` (story A4c): the traded index options after NIFTY's push; one result line per
index, one #fno-desk alert naming every index not recorded, exit 1 if any. Never places orders."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping

from ..alerts.output import announce
from ..alerts.sender import AlertSender
from ..models import now_ist
from ..research_data.calendar import CalendarError
from .indices import IndexRecording
from .recorder import QuoteSnapshotRecorder, RecordResult

INDEX_LINE = "{underlying} {status}: {snapshot_id} ({rows} contracts, complete={complete}){reason}"
INDEX_ALERT = (
    "3 pm index recorder: not recorded today (canonical none): {names}. Data only; NIFTY is separate; the sidecars "
    "in research/data/quotes/groww/ say why."
)
INDEX_CALENDAR_STOP = "3 pm index recorder stopped, nothing recorded: {error} ({file})"
QUIET_STATUSES = ("not a trading day", "already recorded")


def record_indices(build: Callable[[], Mapping[str, QuoteSnapshotRecorder]], alerts: AlertSender, calendar_file: str,
                   now=now_ist, sleep=time.sleep) -> int:  # fmt: skip
    try:
        results = IndexRecording(build(), now, sleep).run()
    except CalendarError as error:
        message = INDEX_CALENDAR_STOP.format(error=error, file=calendar_file)
        print(message)
        announce(alerts, message)
        return 1
    for underlying, result in results.items():
        print(_line(underlying, result))
    missing = [f"{name} ({_why(result)})" for name, result in results.items() if _missing(result)]
    if missing:
        announce(alerts, INDEX_ALERT.format(names="; ".join(missing)))
    return 1 if missing else 0


def _missing(result: RecordResult) -> bool:
    return not result.complete and result.status not in QUIET_STATUSES


def _why(result: RecordResult) -> str:
    return result.reason or result.raw_file_error or ("incomplete" if result.status == "recorded" else result.status)


def _line(underlying: str, result: RecordResult) -> str:
    reason = "".join(f" - {text}" for text in (result.reason, result.raw_file_error) if text)
    return INDEX_LINE.format(underlying=underlying, status=result.status, snapshot_id=result.snapshot_id or "-",
                             rows=result.rows, complete=result.complete, reason=reason)  # fmt: skip
