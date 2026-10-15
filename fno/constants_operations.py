"""Shared names of the daily operations, split out of `fno/constants.py` at its size limit (and imported there):
the desk run's steps (E3), the whole day's steps and their statuses (O1), and the health check's statuses (O8).
Change a value here, not where it is used."""

from __future__ import annotations

__all__ = [
    "RUN_LOG_DECISIONS_STEP",
    "RUN_LOG_EXITS_STEP",
    "DESK_RUN_STEPS",
    "DAILY_RUN_STEPS",
    "OWNER_TIMING_STEP",
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
]

# Story E3: the daily run's step that collects the books' decisions, as its run log names it (read by D3b and S2)
RUN_LOG_DECISIONS_STEP = "decisions"
RUN_LOG_EXITS_STEP = "exits"  # the daily run's exit review step (scoreboard B reads it, story S6)
# E3's steps, then story O1's whole day in order (the health check O8 reads it); Book 1 decides right after the pack
DESK_RUN_STEPS = ("versions", "pack", RUN_LOG_DECISIONS_STEP, "snapshot", "fills", RUN_LOG_EXITS_STEP)
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
    "quotes_done",
    "card",
)  # fmt: skip; the quote parts start first (judge 178)
STEP_OK, STEP_FAILED, STEP_REFUSED, STEP_NOT_LIVE = "ok", "failed", "refused", "not_live"  # an O1 step's status

# The daily health check (story O8, fno/health/): its statuses and its own run record
HEALTH_OK, HEALTH_LATE, HEALTH_MISSED, HEALTH_UNKNOWN = "ok", "late", "missed", "unknown"
HEALTH_NOT_DUE, HEALTH_NOT_EXPECTED = "not due", "not expected"
HEALTH_PROBLEMS = (HEALTH_LATE, HEALTH_MISSED, HEALTH_UNKNOWN)
HEALTH_RUNS_FILE = "research/ops/health_runs.csv"
