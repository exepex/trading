# Wave 0 judgment, round 5 (2026-10-12)

**Verdict: PASS.** All four round-4 findings are closed. No blocking or should-fix finding is open. I found three new minor issues (N18 to N20).

Scope: commit e78b727. `git rev-parse HEAD` returned e78b727ba03bc2f3b4857e59e8330db155e3743a. I did not change any repository file; my probes are in /tmp/judge5.

## Commands and results
- `python -m pytest -q`: 186 passed.
- `ruff check fno tests`: All checks passed.
- `ruff format --check fno tests`: 136 files already formatted.
- File sizes: no .py file in fno/ or tests/ is over 350 lines. runner.py is 309 lines (the LiveRunner class is about 248) and classifier.py is 291.
- `git status --short`: clean after all runs.
- /tmp/judge5/probe_rupee.py: 34 of my own rupee headlines, run at HEAD and at the parent commit. HEAD gets 5 wrong, the parent 17. None of the 5 at HEAD has the wrong sign; 4 score 0 and 1 is ambiguous.
- /tmp/judge5/probe_runner.py p1 to p8: simulated clock runs that tick every minute (every 5 minutes for the outage runs), over up to 64 hours of simulated time.

## Round-4 findings
| # | Status | Evidence |
|---|---|---|
| N16 should fix (rupee "hits") | CLOSED | "Rupee hits one-year peak" +1 (was -1). "record high", "strongest level", "highest in two months" and "day's high" are all +1. "hits record low", "fresh all-time low", "near two-month low" and "session low" are -1. Neutral headlines ("hits 88 per dollar", "hits support at 83") now score 0; before they scored -1. One small regression on the low side, see N19. |
| N14 alert ordering | CLOSED | `_check_news_watcher` now runs first in `tick` (runner.py:108). P8 (dead watcher plus NSE down): the dead-watcher alert goes out. A later problem can no longer take the alert slot first. Side effect: see N20. |
| N15 kill switch across midnight | CLOSED | P1: engaged Mon 11:05, ticks to Wed 16:00. Result: one kill alert, one close_all call, no repeat at midnight. P2: released Tue 10:00 and re-engaged Tue 10:30. The second engagement alerts again at 10:30, as it should. If the switch is released and re-engaged between two ticks (5 s apart), there is no second alert. That only happens if a person does both inside 5 s, so I am not raising it. |
| N17a summary on kill-switch days | CLOSED | P1: a day summary goes out Mon, Tue and Wed at 15:31 while the switch stays engaged. |
| N17b reference alerts | CLOSED | Each outage is now alerted once. No alert at the weekend (P4, Sat 00:00 to Mon 16:00: one alert, on Monday). After recovery the flag resets, and an outage the next day alerts again (P7). A second outage "later the same day" cannot happen: reference data loads once per day and is never reloaded after a success. Timing of the alert: see N18. |

## New findings (all minor)
- **N18 (minor): the outage alert goes out at midnight.**
  - Evidence: in P4, P5, P6 and P7 the only alert is at 00:00 IST, for example "Tue 13 00:00". The builder's test comment says "Tuesday morning only" and its name says "never overnight". Both are wrong.
  - Failure scenario: NSE is down from evening until 10:00. The owner gets one Slack ping at midnight and no reminder at the open, while the desk runs no scans all morning.
  - Startup on a holiday: if the desk starts while NSE is down, it does not know the holidays yet. P6 (Tuesday a holiday) then alerts at Tue 00:00. P6b, with holidays already known from an earlier load, sends no alert.
  - Fix: in `_market_day_ahead`, also require the time to be at or after a pre-market start (for example 08:45, the news window start). Make the test assert the time of the alert.
- **N19 (minor): "lowest" and "weakest" lost their score.**
  - Evidence: "Rupee hits lowest level in a year", "Rupee hits weakest level since 2013" and "Rupee hits the lowest level ever" now score 0. The parent commit scored them -1 (correct). The high side lists highest and strongest; the low side has no lowest or weakest.
  - Fix: change the ending of `RUPEE_HITS_LOW` to `(?:lows?|lowest|weakest)` and add these headlines to the test.
- **N20 (minor, cosmetic): two problem alerts in the same minute at the start of a day.**
  - Cause: the dead-watcher check now runs under the previous day's state. `_start_day_if_needed` then resets the 15-minute limit, so the reference alert can go out straight away.
  - Evidence: P8 sends both alerts at "Tue 13 08:00", in one tick.
  - Fix, optional: keep `last_problem_alert` across the day reset.

No other regressions in runner.py or classifier.py. The kill-switch bookkeeping resets only when the switch is released.

**Final verdict: PASS.** No blocking or should-fix finding is open. N18 to N20 are minor and do not block the wave.