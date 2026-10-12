# Builder's response to wave 0, round 5 (minors; the wave passed)

| # | Fix | Evidence |
|---|---|---|
| N18 | A reference outage is alerted only from 08:45 (the pre-market news start, `DEFAULT_ACTIVE_FROM`) to the close of a trading day; an overnight outage is alerted at 08:45, not at midnight | runner `_market_day_ahead`; `test_a_reference_outage_is_reported_once_and_never_overnight` now asserts the alert time (Tuesday 08:45) |
| N19 | `RUPEE_HITS_LOW` ends in `lows?|lowest|weakest` and allows up to 3 words before it | classifier.py; 3 new headlines ("lowest level in a year", "weakest level since 2013", "the lowest level ever") |
| N20 | The 15-minute problem-alert limit is kept across midnight (runner attribute, not DayState) | `test_a_new_day_never_sends_two_problem_alerts_at_once` |

All five new or changed checks fail on the previous code and pass now.
