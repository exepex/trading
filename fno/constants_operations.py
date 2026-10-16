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
    "STEP_OK",
    "STEP_FAILED",
    "STEP_REFUSED",
    "STEP_NOT_LIVE",
    "HEALTH_OK",
    "HEALTH_LATE",
    "HEALTH_MISSED",
    "HEALTH_UNKNOWN",
    "HEALTH_NOT_DUE",
    "HEALTH_NOT_EXPECTED",
    "HEALTH_PROBLEMS",
    "HEALTH_RUNS_FILE",
    "AI_FIRE_STEP",
    "AI_COLLECT_STEP",
    "ENV_ROUTINE_BOOK2_DECISION_TRIGGER_ID",
    "ENV_ROUTINE_BOOK2_DECISION_TOKEN",
    "ENV_ROUTINE_BOOK3_DECISION_TRIGGER_ID",
    "ENV_ROUTINE_BOOK3_DECISION_TOKEN",
    "ROUTINE_POINTER_MAX_BYTES",
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
AI_FIRE_STEP, AI_COLLECT_STEP = "ai_fire", "ai_collect"  # story F1t: the AI books' decisions, around Book 1's
DAILY_RUN_STEPS = (
    "quotes",
    "margin_check",
    "weather",
    "forecasts_v4",
    *DESK_RUN_STEPS[:2],
    AI_FIRE_STEP,  # right after the pack: a slow Book 1 must not delay the fire (judge 301)
    "book1",
    AI_COLLECT_STEP,  # before E3's deadline step
    *DESK_RUN_STEPS[2:],
    REVIEWS_STEP,
    "quotes_done",
    "card",
    "candles",  # A16b-d: after A16's last mark (fno/intraday/backfill_daily.py)
)  # fmt: skip; the quote parts start first (judge 178)
STEP_OK, STEP_FAILED, STEP_REFUSED, STEP_NOT_LIVE = "ok", "failed", "refused", "not_live"  # an O1 step's status

# The daily health check (story O8, fno/health/): its statuses and its own run record
HEALTH_OK, HEALTH_LATE, HEALTH_MISSED, HEALTH_UNKNOWN = "ok", "late", "missed", "unknown"
HEALTH_NOT_DUE, HEALTH_NOT_EXPECTED = "not due", "not expected"
HEALTH_PROBLEMS = (HEALTH_LATE, HEALTH_MISSED, HEALTH_UNKNOWN)
HEALTH_RUNS_FILE = "research/ops/health_runs.csv"

# Story F1t: each AI book's decision routine (two more routines, made by the owner; the forecast routines are
# separate), fired by the daily run, so these are settings of the daily routine's environment (names only here)
ENV_ROUTINE_BOOK2_DECISION_TRIGGER_ID = "FNO_ROUTINE_BOOK2_DECISION_TRIGGER_ID"
ENV_ROUTINE_BOOK2_DECISION_TOKEN = "FNO_ROUTINE_BOOK2_DECISION_TOKEN"
ENV_ROUTINE_BOOK3_DECISION_TRIGGER_ID = "FNO_ROUTINE_BOOK3_DECISION_TRIGGER_ID"
ENV_ROUTINE_BOOK3_DECISION_TOKEN = "FNO_ROUTINE_BOOK3_DECISION_TOKEN"
# The routine API's text limit as F1t and G11 use it (one home, agreed with G11's owner 16 Oct): unmeasured, confirmed
# by the go-live test fire; a pointer over it is not sent, never truncated
ROUTINE_POINTER_MAX_BYTES = 64 * 1024
