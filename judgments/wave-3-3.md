# Wave 3 judgment, round 3 (2026-10-12)

I checked HEAD e78b727, the commit with the fixes, against its parent. **Verdict: PASS.** No blocking or should-fix findings are left open. All six round-2 findings are closed. I found no new defects and no regressions. Nothing in the change can make a trade bigger or get around a limit.


## Commands and results
- **Checkout:** `git fetch origin claude/beautiful-pascal-566jb5 && git checkout --detach e78b727` worked. HEAD is e78b727 ("Fix the judge's findings: wave 0 round 4 and wave 3 round 2").
- **Tests:** `python -m pytest -q` gave 186 passed (176 in round 2).
- **Lint:** `ruff check fno tests` gave "All checks passed!".
- **Format:** `ruff format --check fno tests` gave "136 files already formatted".
- **Backtest:** `python -m fno backtest NIFTY --days 10 --out /tmp/bt` exited 0.
  - 8 trades, 62% won, net +Rs 6,105, 10 sessions, 1 trade still open when the data ended.
  - Exits: stop 3 + target 2 + trailing 3 = 8.
  - The new per-name pause wording is printed in the disclaimer.
  - Round 2 showed +Rs 7,650 because Yahoo's 10-day window has moved forward with today's session. That is not a code change.
- **File sizes:** html_report.py is 722 lines and exempt. The next largest are services.py 337, strategies.py 321, journal.py 320 and runner.py 309. No file is over 350.
- **Clean tree:** `git status --short` is empty after all runs. My probes are in /tmp/judge3.

## Round-2 findings
| # | Status | Evidence |
|---|---|---|
| N1 (should fix): feed-down alert lost to the rate limit | CLOSED | price_watch.py `_back_off` now stores what `report(...)` returns, and `report` is typed `Callable[[datetime, str], bool]`. Probe /tmp/judge3/n1_probe.py uses the real `LiveRunner._report_problem`, with another problem alert sent 1 minute before the feed fails, then 3 hours of failure. Calling `_watch_prices_if_due` directly: exactly 1 feed alert and 17 feed calls. Driving the whole `runner.tick`: also exactly 1. After 10 minutes of recovery, failures are 0 and the "already reported" flag is cleared. A new 30-minute outage then sends a second alert (2 in total) in both modes. A 1-minute "recovery" falls inside the 15-minute pause, so it counts as the same outage and gives no extra alert, which is correct. The new test `test_the_feed_down_alert_is_not_lost_to_the_rate_limit` asserts exactly 1 alert. |
| N2 (minor): one unguarded call loses all groww-check output | CLOSED | groww_check.py wraps the raw diagnostic call in try/except. Probe /tmp/judge3/n2_probe.py uses a fake Groww where the second `get_ltp` raises TimeoutError. All 7 earlier lines are kept, plus "not priced: NIFTY, BANKNIFTY, FINNIFTY; raw check FAILED: TimeoutError: second call timed out". No repo test covers this; the probe does. |
| N3 (minor): per-name post-loss pause not disclosed | CLOSED | The DISCLAIMER says "the post-loss pause per name, not account-wide as on the desk", and WAVES W3.2 says the same. The wording is accurate: on the desk the 30-minute re-entry pause is per name (risk_gate.py:113 uses `idea.underlying`), and only the post-loss pause is account-wide. |
| N4 (minor): source names repeated as literals | CLOSED | services.py:78 is `{NSE_SOURCE: ..., BSE_SOURCE: ...}`. The strings "NSE filings" and "BSE filings" now appear only in exchange_sources.py:18/23. |
| N5 (minor): cooldown test misses the after-win branch | CLOSED, and the test is not vacuous | Probe /tmp/judge3/n5_probe.py runs the test's own rally. With `Cooldowns()`: 5 trades, all won, all exits at target, smallest gap 30.0 minutes. With the re-entry pause set to 0: 6 trades, smallest gap 0, so the test would fail. With it set to 15: smallest gap 15, so the test would fail. |
| N6 (minor): missing-price log keyed on host date | CLOSED | The log is keyed on `now.astimezone(IST).date()`. Probe /tmp/judge3/n6_probe.py checks at 18:00 and 19:00 UTC on 12 Oct (the same UTC date, but different IST dates). It logs twice, and the key is 2026-10-13. |

## Regression checks
- **price_watch.py:** A successful check still resets failures, the pause and the "already reported" flag, so recovery works. Back-off is unchanged: 17 calls in 3 hours, the same as round 2. `_report_problem` is the only production caller, and it already returns a bool. Every test lambda now returns True.
- **runner.py:**
  - The commit also contains wave-0 changes. Moving `_check_news_watcher` before `_start_day_if_needed` does not touch the price watch.
  - The price watch still runs only in active phases and while the kill switch is off. Both whole-tick probes behaved the same as the direct calls.
- **groww_check.py, services.py and backtest/report.py:** The changes are only those described above. Ruff is clean, and none of these imports creates a cycle that the test suite would miss: 186 tests pass, and the CLI backtest ran.
- **New tests** (test_runner_alerts.py, the new test_shock and test_backtest cases): all pass and do not write repo data. The git tree is clean afterwards.

## New findings
No blocking or should-fix findings. Two observations, neither of which needs a fix:
- **Late feed-down alert.** The alert is retried only when the feed fails again. Because those attempts back off, it can arrive up to about 15 minutes after the alert slot frees up. In the probe the slot freed at 11:14 and the alert went out at 11:21. The alert still always goes out.
- **Docstring wording.** The `Cooldowns` docstring in simulator.py:45 says "The desk's entry pauses". It is slightly loose now that the per-name difference is disclosed. That disclosure is in the report and WAVES, so it is cosmetic only.

## Verdict
**PASS.** All round-2 findings (N1 should-fix, N2-N6 minor) are closed, with evidence from my own probes. There are no new blocking or should-fix findings.