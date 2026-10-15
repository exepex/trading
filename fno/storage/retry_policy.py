"""How an NSE download treats each answer (story A9b): what is worth another try, how long to wait, and when to stop.

- retried: no connection, a timeout or a cut answer, HTTP 429 and every 5xx, at most `len(RETRY_WAITS) + 1` tries;
- refused, never retried: 403 and every other 4xx but 404 (retrying a refusal invites a longer block; the pacer
  pauses a host after two refusals in a row);
- `Retry-After` on a retried answer stretches the wait; above `MAX_RETRY_AFTER_SECONDS` the download stops at once.
  Reasoning only: past two minutes NSE is blocking, not hiccuping; the pacer's 15-minute pause and the next scheduled
  run are the right retry. Worst case per file: 65 s of waits, or 3 x 120 s; A12's deadline-bound backfill
  (`filings archive --max-minutes`) can lose up to 6 minutes to one file before it stops at its deadline.
"""

from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime

RETRY_WAITS = (5, 15, 45)  # seconds before tries 2, 3 and 4
MAX_RETRY_AFTER_SECONDS = 120
TOO_MANY_REQUESTS, NOT_FOUND = 429, 404
OK, RETRY, REFUSED = "ok", "retry", "refused"


def verdict(status: int) -> str:
    """What an HTTP status means for the download (404 is the caller's: not published)."""
    if status == TOO_MANY_REQUESTS or 500 <= status <= 599:
        return RETRY
    if 400 <= status <= 499:
        return REFUSED
    return OK


def retry_after_seconds(header: str | None, now: datetime) -> float | None:
    """`Retry-After` in seconds (a number or an HTTP date); None when absent, malformed or already past."""
    if not header:
        return None
    text = header.strip()
    if text.isdigit():
        return float(text)
    try:
        moment = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None
    if moment is None or moment.tzinfo is None:
        return None
    seconds = (moment - now).total_seconds()
    return seconds if seconds > 0 else None
