"""The same-day announcements poll's fixed names (story A21 part 2), used only by `fno/announcements_live/`."""

from datetime import time

JOB = "announcements_live"
WRITER = "announcements-live"
WINDOW_FIRST, WINDOW_LAST = time(9, 15), time(14, 0)  # A16's marks inside the window (20 of them)
NO_POLL_BY = time(10, 0)
STALE_MINUTES = 60
REQUEST_TIMEOUT = (2.0, 3.0)  # connect, read: 5 s in all, no retry inside a mark (A16 owner's condition)
MEMBER_TIME_LIMIT_SECONDS = 10.0  # the request plus the Drive writes (A16 owner and LM1 builder, 16 Oct 2026)

ITEMS_TABLE, POLLS_TABLE, RAW_FOLDER = "announcements/items", "announcements/polls", "announcements/raw"
ITEM_COLUMNS = ("seq_id", "symbol", "isin", "desc", "an_dt", "exchdisstime", "attachment_url", "first_seen_at",
                "run_id")  # fmt: skip
POLL_COLUMNS = ("mark", "requested_at", "status", "kind", "items", "new_items", "run_id")
OK, FAILED, MISSED_WINDOW = "ok", "failed", "missed_window"
