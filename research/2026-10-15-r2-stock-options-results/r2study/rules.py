"""Every fixed number of the R2 protocol (PROTOCOL.md) and of pre-run amendment 1, in one place.

Each value cites its section. None is tuned: they were all written before any data of the study was read.
"""

from __future__ import annotations

import math
from datetime import date

# PROTOCOL.md section 3: periods
PERIOD_START = date(2019, 1, 1)  # first reaction session of the study
DECISION_START = date(2024, 10, 1)  # the decision window starts here; earlier events are descriptive only
CORRELATION_YEARS = (2019, 2020, 2021)  # the only years whose event moves are read (section 7)

# section 3: lot size of the legacy format
LOT_WINDOW_SESSIONS = 5  # sessions ending at the entry session
LOT_AGREEING_SESSIONS = 3  # the same derived value on at least this many of them
LOT_VALIDATION_MIN_SHARE = 0.98  # exact matches with the current format's column on the overlap

# section 4: timing
MARKET_OPEN, MARKET_CLOSE = (9, 15), (15, 30)  # IST
MIN_SESSIONS_AFTER_R = 5  # the expiry is at least this many sessions after the reaction session

# section 5: caps and liquidity
MAX_LOSS_CAP_RS = 10_000.0
MIN_CONTRACTS_TRADED = 50  # every leg, on the entry session and on the exit session
MIN_OPEN_INTEREST_CONTRACTS = 100  # every leg, on the entry session

# section 6: costs
ASSUMED_HURDLE = 0.05  # e: the assumed hurdle (FACTORY_RULES.md section 2, judge 97), not a conservative bound
S7_TAIL_SHARE = 0.02  # T for the short iron condor: 2% of its maximum loss
PAD_PERCENTILE = 75  # the bucket's 75th-percentile half-spread
THIN_MARGIN_RATIO = 2.0  # gross/cost below this prints `thin margin` (a warning only)

# section 6.2: the snapshot's buckets
BUCKET_MIN_LEGS = 30
BUCKET_MAX_ONE_SIDED_SHARE = 0.20  # more than this share of legs without a bid or an ask: the bucket is untradable
SNAPSHOT_STEPS = 3  # K0 - 3 steps to K0 + 3 steps
SNAPSHOT_LOOKAHEAD_SESSIONS = 10

# section 7: clusters and correlation
BOOTSTRAP_RESAMPLES = 2_000
BOOTSTRAP_SEED = 20261015
BOOTSTRAP_INTERVAL = (5.0, 95.0)  # percentiles of the 90% interval
UNKNOWN_SECTOR = "unknown"

# section 8: the decision
MIN_FIT_SHARE = 0.25
MIN_CLUSTERS_A_YEAR = 130  # the registered rule; it alone decides criterion 3
YEARS_TO_REACH_SAMPLE = 3
Z_ALPHA_ONE_SIDED_5 = 1.645
Z_BETA_80_POWER = 0.842  # amendment 1 section C: shown beside the rule, never deciding
ASSUMED_SD_SHARE = 0.60  # SD of a trade's outcome as a share of the structure's price (reasoning only)

# section 9: stage 0
MIN_RESULTS_DATE_COVERAGE = 0.80
MAX_LOT_UNKNOWN_SHARE = 0.10

# amendment 1, section D
DUPLICATE_MEETING_DAYS = 30  # results meetings of one stock fewer than this many days apart are one event
FILING_SEARCH_DAYS = 3  # a results filing is looked for from the entry session's date to D + 3 days
RESULTS_PURPOSE = "financial result"
DAYS_A_YEAR = 365.25


def units_needed(z_alpha: float, z_beta: float, sd: float, net: float) -> int:
    """G3's sample size n = ((z_alpha + z_beta) x SD / net)^2, rounded up. z_beta = 0 is the registered form (50%
    power at the assumed effect); z_beta = 0.842 gives 80% power."""
    return math.ceil(((z_alpha + z_beta) * sd / net) ** 2)


def clusters_a_year_needed(z_beta: float) -> int:
    """Independent units a year to reach n within YEARS_TO_REACH_SAMPLE years."""
    n = units_needed(Z_ALPHA_ONE_SIDED_5, z_beta, ASSUMED_SD_SHARE, ASSUMED_HURDLE)
    return math.ceil(n / YEARS_TO_REACH_SAMPLE)


def window_years(first: date, last: date) -> float:
    """Length of a window in years, both ends included (amendment 1 section A)."""
    return ((last - first).days + 1) / DAYS_A_YEAR


def clusters_a_year(count: int, first: date, last: date) -> float:
    """Criterion 3's rate: clusters counted in the window / the window's length in years."""
    return count / window_years(first, last)
