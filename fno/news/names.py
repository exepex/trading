"""Fixed names of story A19 (kept here because `fno/constants.py` is at the 350-line limit): the job, its Drive
areas, record kinds and failure kinds. Messages built from these never carry an item's headline or link."""

JOB = "news-capture"
KICK_JOB = "news-capture-kick"
WRITER = "news-capture"

# Drive paths inside O9's `data` area
PARTS_FOLDER, SEEN_FOLDER = "news/parts", "news/seen"

# Line kinds of a part
POLL_LINE, ITEM_LINE = "poll", "item"

# Outcome of one feed in one poll
NEW, NOTHING_NEW, NOT_MODIFIED, FAILED = "new", "nothing_new", "not_modified", "failed"

# Failure kinds of a feed (scope 8)
HTTP_ERROR, NOT_XML, NO_ITEMS, NO_TIMES, STALE, BEYOND_WINDOW = (
    "http_error",
    "not_xml",
    "no_items",
    "no_times",
    "stale",
    "beyond_window",
)
# Failure kinds of a run (the step is the kind's own name)
DRIVE_WRITE, RECEIPT_COMMIT, SEEN_SET_LOAD, CLOCK, DISPATCH, COVERAGE_GAP, RESTART_STOPPED = (
    "drive_write",
    "receipt_commit",
    "seen_set_load",
    "clock",
    "dispatch",
    "coverage_gap",
    "restart_stopped",
)
RECOVERED_SUFFIX = "_recovered"

# Feed kinds and published-time precision
PUBLISHER, OFFICIAL = "publisher", "official"
SECOND, DAY = "second", "day"
