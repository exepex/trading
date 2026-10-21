"""`python -m fno global-cues preopen` (story A17e part B), started by A22's pre-open routine beside its own command
(both run from about 08:36 IST in one checkout). It waits for its own window on its own clock: no read starts before
`WINDOW_OPENS` or after `WINDOW_CLOSES` (an index not reached by then is a failure), so its commit (its snapshot logs
and, after a failure, O10's row; pulled with `--no-rebase`, the push retried) is done before A22's push at about 09:11.

One line per Asian index. Any failure, from building the reader (Drive settings missing, an expired Drive sign-in) to
one index's read, posts one #fno-desk line naming what failed and appends one row to O10's capture-error log (a
routine, not a workflow: O10's `record-error` row), then exits 1; so does a morning where no open market gave a live
level (every one `stale`: Yahoo's feed paused). Lines and the alert name indexes, statuses and error classes only,
never a level (private, owner rule 50a79a43)."""

from __future__ import annotations

import time as clock_time
from collections.abc import Callable
from datetime import datetime, time

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
WINDOW_OPENS, WINDOW_CLOSES = time(8, 50), time(9, 5)  # IST: after A22's GIFT Nifty read, before its pre-open read
CLOSED_WINDOW = "{index}: FAILED, not read: the window closed at 09:05 IST"
NOT_COMMITTED_MARK = "NOT committed"


def cmd_preopen(out=print, now: Callable[[], datetime] | None = None, sleep=clock_time.sleep) -> int:
    from ..models import now_ist
    from .wiring import build_preopen, build_preopen_committers

    now = now or now_ist
    _wait_for_window(now, sleep)
    try:
        reader, sources = build_preopen()
    except FAILURES as exc:
        out(f"preopen: STOPPED before any read ({type(exc).__name__})")
        return _report(out, f"stopped before any read ({type(exc).__name__})") | _commit(out, build_preopen_committers)
    code = _read_all(out, reader, sources, now)
    return code | _commit(out, build_preopen_committers)


def _wait_for_window(now: Callable[[], datetime], sleep) -> None:
    current = now()
    opens = datetime.combine(current.date(), WINDOW_OPENS, tzinfo=current.tzinfo)
    if (wait := (opens - current).total_seconds()) > 0:
        sleep(wait)


def _read_all(out, reader, sources, now: Callable[[], datetime]) -> int:
    failed, statuses = [], []
    for index, source in sources:
        if now().time() >= WINDOW_CLOSES:
            failed.append(index)
            out(CLOSED_WINDOW.format(index=index))
            continue
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


def _commit(out, committers: Callable[[], list]) -> int:
    """Its own files only (owned paths), whatever the reads gave; 1 when they could not be pushed (alerted)."""
    try:
        lines = [committer.commit("pre-open Asian levels") for committer in committers()]
    except FAILURES as exc:
        lines = [f"pre-open receipts {NOT_COMMITTED_MARK}: {type(exc).__name__}"]
    for line in lines:
        out(line)
    unsaved = [line for line in lines if NOT_COMMITTED_MARK in line]
    return _report(out, "receipts not committed (the routine's output names why)") if unsaved else 0


def _report(out, what: str) -> int:
    """One #fno-desk line and one O10 row; exit code 1."""
    from ..composition import build_alert_sender
    from ..health.capture_errors import CaptureError, one_line
    from ..health.wiring import build_capture_error_log
    from ..models import now_ist

    out(build_alert_sender().send(ALERT.format(what=what)))
    build_capture_error_log().append(CaptureError(now_ist().date(), JOB, STEP, "failure", one_line(what), ""))
    return 1
