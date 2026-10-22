"""Shared names of the daily operations, split out of `fno/constants.py` at its size limit (and imported there):
the desk run's steps (E3), the whole day's steps and their statuses (O1), and the health check's statuses (O8).
Change a value here, not where it is used."""

from __future__ import annotations

__all__ = [
    "RUN_LOG_DECISIONS_STEP",
    "RUN_LOG_EXITS_STEP",
    "RUN_LOG_TRADE_MARKS_STEP",
    "REVIEWS_STEP",
    "DESK_RUN_STEPS",
    "DAILY_RUN_STEPS",
    "OWNER_TIMING_STEP",
    "STEP_OK",
    "STEP_FAILED",
    "STEP_REFUSED",
    "STEP_NOT_LIVE",
    "STEP_FROZEN",
    "DESK_FROZEN_STEPS",
    "OPEN_POSITION_STEPS",
    "HEALTH_OK",
    "HEALTH_LATE",
    "HEALTH_MISSED",
    "HEALTH_UNKNOWN",
    "HEALTH_NOT_DUE",
    "HEALTH_NOT_EXPECTED",
    "HEALTH_PROBLEMS",
    "HEALTH_RUNS_FILE",
]

# Story E3: the daily run's step that collects the books' decisions, as its run log names it (read by D3b and S2)
RUN_LOG_DECISIONS_STEP = "decisions"
RUN_LOG_EXITS_STEP = "exits"  # the daily run's exit review step (scoreboard B reads it, story S6)
RUN_LOG_TRADE_MARKS_STEP = "trade_marks"  # E2d: every open trade marked right after the exits
REVIEWS_STEP = "reviews"  # after the exits: E6's scorecards and automatic pauses (LR3's drift monitor joins it later)
# E3's steps (with E2d's marking), then story O1's whole day in order (the health check O8 reads it); Book 1 decides
# right after the pack
DESK_RUN_STEPS = (
    "versions",
    "pack",
    RUN_LOG_DECISIONS_STEP,
    "snapshot",
    "fills",
    RUN_LOG_EXITS_STEP,
    RUN_LOG_TRADE_MARKS_STEP,
)
OWNER_TIMING_STEP = "owner_timing_fills"  # story E8: right after the quote parts start, before every other step
DAILY_RUN_STEPS = (
    "quotes",
    OWNER_TIMING_STEP,
    "margin_check",
    "weather",
    "forecasts_v4",
    *DESK_RUN_STEPS[:2],
    "book1",
    *DESK_RUN_STEPS[2:],
    REVIEWS_STEP,
    "quotes_done",
    "card",
    "price_distribution",  # story G13: reads the committed 3 pm chains, nothing reads it, so after the card
    "premium_ranges",  # story G13d: from G13's record, at once (sealed by 15:30; the command refuses after it)
    "price_distribution_scores",  # G13's scores: outcomes lag one session (NSE's close file lands in the evening)
    "price_ranges",  # story G13b: the 15:45 ranges from the same chains, after G13
    "price_range_scores",  # G13b's scores and seals; the same one-session lag
    "premium_range_scores",  # G13d's scores and seals: issues whose next session has passed
    "candles",  # A16b-d: after A16's last mark (fno/intraday/backfill_daily.py)
    "close_read",  # story A4h: today's closes from NSE's index list, 15:40, after the candles
    "close_recheck",  # A4h's second read, 16:00, last (judge 440 add. 1)
)  # fmt: skip; the quote parts start first (judge 178)
STEP_OK, STEP_FAILED, STEP_REFUSED, STEP_NOT_LIVE = "ok", "failed", "refused", "not_live"  # an O1 step's status
STEP_FROZEN = "frozen"  # story O1-desk-freeze: a desk step the owner froze (config.yaml desk.frozen); not a failure
# The paper desk's daily steps the freeze stops (owner's cut-list, 22 Oct); every other step of the day runs as ever
DESK_FROZEN_STEPS = (*DESK_RUN_STEPS, "book1", OWNER_TIMING_STEP, REVIEWS_STEP, "card")
# What an open position needs, so they run while any book holds one: its prices (the pack's spot and the execution
# snapshot, which the exits' data gate reads), its exits, its marks and E6's loss rules on it
OPEN_POSITION_STEPS = ("pack", "snapshot", RUN_LOG_EXITS_STEP, RUN_LOG_TRADE_MARKS_STEP, REVIEWS_STEP)

# The daily health check (story O8, fno/health/): its statuses and its own run record
HEALTH_OK, HEALTH_LATE, HEALTH_MISSED, HEALTH_UNKNOWN = "ok", "late", "missed", "unknown"
HEALTH_NOT_DUE, HEALTH_NOT_EXPECTED = "not due", "not expected"
HEALTH_PROBLEMS = (HEALTH_LATE, HEALTH_MISSED, HEALTH_UNKNOWN)
HEALTH_RUNS_FILE = "research/ops/health_runs.csv"
