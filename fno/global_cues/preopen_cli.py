"""`python -m fno global-cues preopen` (story A17e part B), run by A22's pre-open routine at about 08:50-09:05 IST.

One line per Asian index. Any failure, from building the reader (Drive settings missing, an expired Drive sign-in) to
one index's read, posts one #fno-desk line naming what failed and appends one row to O10's capture-error log (a
routine, not a workflow: O10's `record-error` row), then exits 1; so does a morning where no open market gave a live
level (every one `stale`: Yahoo's feed paused). Lines and the alert name indexes, statuses and error classes only,
never a level (private, owner rule 50a79a43)."""

from __future__ import annotations

import requests

from .preopen import LIVE, STALE

# every failure one index's read can meet: the network (a block included), the answer, Drive, the private table
FAILURES = (
    requests.RequestException,
    ValueError,
    KeyError,
    TypeError,
    IndexError,
    ArithmeticError,
    RuntimeError,
    OSError,
)
JOB, STEP = "global-cues-preopen", "preopen"
ALERT = "Omenix F&O pre-open Asian levels: {what} (the routine's output names why)"
ALL_STALE = "no live level: every open market stale"


def cmd_preopen(out=print) -> int:
    from .wiring import build_preopen

    try:
        reader, sources = build_preopen()
    except FAILURES as exc:
        out(f"preopen: STOPPED before any read ({type(exc).__name__})")
        return _report(out, f"stopped before any read ({type(exc).__name__})")
    failed, statuses = [], []
    for index, source in sources:
        try:
            line, status = reader.read(source, index)
        except FAILURES as exc:
            failed.append(index)
            out(f"{index}: FAILED ({type(exc).__name__}): {exc}")
            continue
        out(line)
        statuses.append(status)
    if failed:
        return _report(out, f"{', '.join(failed)} failed")
    if STALE in statuses and LIVE not in statuses:
        return _report(out, ALL_STALE)
    return 0


def _report(out, what: str) -> int:
    """One #fno-desk line and one O10 row; exit code 1."""
    from ..composition import build_alert_sender
    from ..health.capture_errors import CaptureError, one_line
    from ..health.wiring import build_capture_error_log
    from ..models import now_ist

    out(build_alert_sender().send(ALERT.format(what=what)))
    build_capture_error_log().append(CaptureError(now_ist().date(), JOB, STEP, "failure", one_line(what), ""))
    return 1
