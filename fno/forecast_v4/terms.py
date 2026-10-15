"""The registered numbers of protocol v4 (PROTOCOL_v4.md sections 1, 4 and 5): horizons, block lengths, the bootstrap,
the minimum effects, the confirmatory family and its two looks."""

from __future__ import annotations

from ..constants import (
    V1_RV_1S,
    V2_RV_5S,
    V3_RV_20S,
    V4_BASELINE_BASE_RATE,
    V4_BASELINE_HAR_DAILY,
    V4_BASELINE_OPTION_IMPLIED_PROB,
    V4_BASELINE_PREMIUM_ADJUSTED,
    V4_RV_BELOW_WEEKLY_IV,
    V4_SLOTS,
    V5_INSIDE_STRADDLE,
    V6_BIG_MOVE_1S,
    V6_BIG_MOVE_5S,
    V7_VIX_UP_5S,
)

SESSIONS_A_YEAR = 252  # the session clock of every annualised volatility
CALENDAR_DAYS_A_YEAR = 365  # the calendar clock of quoted implied volatility
BIG_MOVE = 0.02  # V6: absolute log return of at least 2%

HORIZON_SESSIONS = {
    V1_RV_1S: 1,
    V2_RV_5S: 5,
    V3_RV_20S: 20,
    V4_RV_BELOW_WEEKLY_IV: 5,
    V5_INSIDE_STRADDLE: 20,
    V6_BIG_MOVE_1S: 1,
    V6_BIG_MOVE_5S: 5,
    V7_VIX_UP_5S: 5,
}  # V5 runs to its expiry: 20 only sets its block and its outcomes a year
BLOCK_LENGTH = {
    V1_RV_1S: 5, V6_BIG_MOVE_1S: 5, V2_RV_5S: 10, V4_RV_BELOW_WEEKLY_IV: 10, V6_BIG_MOVE_5S: 10, V7_VIX_UP_5S: 10,
    V3_RV_20S: 20, V5_INSIDE_STRADDLE: 20,
}  # fmt: skip
POINT_QUESTIONS = frozenset({V1_RV_1S, V2_RV_5S, V3_RV_20S})  # scored by the QLIKE ranking loss
PRIMARY_BASELINE = {
    V1_RV_1S: V4_BASELINE_HAR_DAILY,  # HAR intraday replaces it once eligible (eligibility.py)
    V2_RV_5S: V4_BASELINE_PREMIUM_ADJUSTED, V3_RV_20S: V4_BASELINE_PREMIUM_ADJUSTED,
    V4_RV_BELOW_WEEKLY_IV: V4_BASELINE_BASE_RATE, V5_INSIDE_STRADDLE: V4_BASELINE_OPTION_IMPLIED_PROB,
    V6_BIG_MOVE_1S: V4_BASELINE_BASE_RATE, V6_BIG_MOVE_5S: V4_BASELINE_BASE_RATE, V7_VIX_UP_5S: V4_BASELINE_BASE_RATE,
}  # fmt: skip

RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261015  # comparison k seeds numpy's SeedSequence([BOOTSTRAP_SEED, k])
FUTILITY_CONFIDENCE = 0.975  # one-sided, at each of the two looks (Bonferroni 2 x 2.5%, ChatGPT review 99)

QLIKE_MIN_EFFECT = 0.03  # mean paired difference <= -3% of the baseline's mean textbook QLIKE, on RV > 0 dates
BRIER_MIN_EFFECT = 0.02  # Brier skill score against the primary baseline

# The confirmatory family: 5 judgeable targets x 3 forecaster slots = 15 members, numbered in this order (seed word k).
# V3 and V5 (20-session) and V4 (diagnostic) are scored and reported the same way but are never members.
FAMILY_QUESTIONS = (V1_RV_1S, V2_RV_5S, V6_BIG_MOVE_1S, V6_BIG_MOVE_5S, V7_VIX_UP_5S)
FAMILY = tuple((q, slot) for q in FAMILY_QUESTIONS for slot in V4_SLOTS)
FAMILY_SIZE = len(FAMILY)
REPORTED_ONLY = (V3_RV_20S, V4_RV_BELOW_WEEKLY_IV, V5_INSIDE_STRADDLE)
# Revision 6 (ChatGPT review 101): no measured rule holds V7's size across VIX regimes, so its three members keep their
# slots at p = 1 (never a claim, never futile) and are left out of the stop rule's Test A (`v4_vix_null.md`).
DESCRIPTIVE_ONLY = frozenset({V7_VIX_UP_5S})

# At most two confirmatory looks; their family-wise rates add to 5% (Bonferroni over looks).
LOOK_STOP_REVIEW, LOOK_SETTLE_DATE = "stop_rule_review", "projected_settle_date"
LOOK_ERROR_RATE = {LOOK_STOP_REVIEW: 0.02, LOOK_SETTLE_DATE: 0.03}
LOOK_NUMBER = {LOOK_STOP_REVIEW: 1, LOOK_SETTLE_DATE: 2}  # the futility bound's last seed word

POWER_REPORT_AT = 60  # scored outcomes of a question before its noise ratio r is measured
POWER = 0.80
USEFUL_TIME_YEARS = 2  # a projected settle date later than this is reported as "cannot settle in useful time"


def min_pairs(question: str) -> int:
    """Fewer paired dates than two blocks: not tested, p = 1."""
    return 2 * BLOCK_LENGTH[question]


def family_seed_word(question: str, slot: str) -> int:
    """1-based position in FAMILY; reported-only comparisons are numbered after it by G8."""
    return FAMILY.index((question, slot)) + 1
