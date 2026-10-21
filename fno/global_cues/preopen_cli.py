"""`python -m fno global-cues preopen` (story A17e part B), run by A22's pre-open routine at about 08:50-09:05 IST.

One line per Asian index. When any index failed, it posts one #fno-desk line naming them and appends one row to O10's
capture-error log (a routine, not a workflow: O10's `record-error` row), then exits 1. Lines and the alert name
indexes, statuses and error classes only, never a level (private, owner rule 50a79a43)."""

from __future__ import annotations

import requests

FAILURES = (requests.RequestException, ValueError, KeyError, TypeError)
JOB, STEP = "global-cues-preopen", "preopen"
ALERT = "Omenix F&O pre-open Asian levels: {failed} failed (the routine's output names why)"


def cmd_preopen(out=print) -> int:
    from ..composition import build_alert_sender
    from ..health.capture_errors import CaptureError, one_line
    from ..health.wiring import build_capture_error_log
    from ..models import now_ist
    from .wiring import build_preopen

    reader, sources = build_preopen()
    failed = []
    for index, source in sources:
        try:
            out(reader.read(source, index))
        except FAILURES as exc:
            failed.append(index)
            out(f"{index}: FAILED ({type(exc).__name__}): {exc}")
    if not failed:
        return 0
    names = ", ".join(failed)
    out(build_alert_sender().send(ALERT.format(failed=names)))
    message = one_line(f"failed: {names}")
    build_capture_error_log().append(CaptureError(now_ist().date(), JOB, STEP, "failure", message, ""))
    return 1
