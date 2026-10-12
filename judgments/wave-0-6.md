# Wave 0 judgment, round 6 (2026-10-12)

**Verdict: PASS.** N18, N19 and N20 are all closed. The N19 fix introduced one new minor regression (N21): some rupee headlines that say the rupee hit a high now score -1, the wrong sign. No blocking or should-fix finding is open.

Scope: HEAD is c27fc67 (`git rev-parse HEAD` returned c27fc67a06a73df466e52d65c6420412bf1d2b14). The parent, ba5c70f, only saved the wave 3 verdict and reworded the `Cooldowns` docstring in fno/backtest/simulator.py. It has no logic change. I did not change any repository file. My probes are in /tmp/judge6. I did not write a `judgments/` file, as you instructed.

## Commands and results
- `git fetch origin claude/beautiful-pascal-566jb5 && git checkout --detach c27fc67`: OK.
- `python -m pytest -q`: 190 passed.
- `ruff check fno tests`: All checks passed.
- `ruff format --check fno tests`: 136 files already formatted.
- File sizes: no .py file is over 350 lines (fno/html_report.py exempt). The largest are fno/live/services.py at 337 lines and fno/strategies.py at 321. runner.py is about 310.
- `git status --short`: clean afterwards.
- Builder's claim that the five new or changed checks fail on the old code: confirmed. I exported ba5c70f to /tmp/judge6/parent with `git archive` and ran the new tests there: 5 failed, 36 passed.
- /tmp/judge6/probe_runner.py (scenarios p1 to p12) and /tmp/judge6/p13.py (P13, P14): simulated-clock runs.
- /tmp/judge6/probe_rupee.py: 27 rupee headlines.
- /tmp/judge6/probe_rupee_old_new.py: scores the same headlines with the old and the new low pattern.

## Round-5 findings
| # | Status | Evidence |
|---|---|---|
| N18 outage alert at midnight | CLOSED | **Overnight outage:** NSE down Mon 16:00 to Tue 16:00 (P5) gives one alert, at Tue 08:45. **Weekend:** NSE down Sat 00:00 to Mon 16:00 (P4) gives one alert, at Mon 08:45. Nothing on Saturday or Sunday. **Known holiday:** Tuesday a holiday that the desk already knows (P6b, P13) gives no alert on Tuesday and one at Wed 08:45. **Recovery, then a new outage the next day (P7):** alerts at Tue 08:45 and again at Wed 08:45. **Outage starting at 08:41 (P12):** alerted at 08:46. **Outage ending at 08:50 (P14):** one alert, at 08:45. **Startup on a holiday with the holidays unknown (P6, P9):** the desk alerts at 08:45 on the holiday itself, because without loaded data it treats every weekday as a trading day. The message is true (the data really could not load), and it no longer comes at midnight. Side effect: if the same outage lasts into Wednesday, the real trading day gets no new alert, because the outage counts as already reported. This needs a startup during an outage lasting over 40 hours, so I am not raising it. |
| N19 "lowest/weakest" | CLOSED | "Rupee hits lowest level in a year", "weakest level since 2013", "the lowest level ever", "a fresh lowest close", "its weakest level" and "weakest" all score -1. "Rupee hits low ahead of Fed" scores -1 (correct); "Rupee hits high ahead of Fed" scores +1. However, allowing 3 words before the low made some high headlines score -1: see N21. |
| N20 alert limit across midnight | CLOSED | The 15-minute limit is now `self._last_problem_alert` on the runner, not part of the per-day state. **Two alerts at the start of a day (P8):** the dead-watcher alert goes out at Tue 08:00 and the reference alert at 08:45, no longer both in the same tick. **No needed alert held back for ever:** the limit is time-only, and every caller retries. The watcher check runs first in every tick; the reference load retries every 5 minutes. P10 makes every tick fail and kills the watcher at 10:00. The watcher alert goes out at 10:05, held back once by the 09:50 alert, and the error alerts carry on every 15 minutes after it. **Kill-switch alerts are not rate-limited:** they use `alerts.kill_switch`, not `_report_problem`. P11: a problem alert at Mon 23:55, then the kill switch engaged at Tue 00:05; the kill alert goes out at 00:05. P1 and P2 from round 5 give the same results as before: one kill alert, and a second one after release and re-engagement. |

## New findings
- **N21 (minor; a regression from the N19 fix): some rupee "high" headlines now score -1 (wrong sign).**
  - Cause: `RUPEE_HITS_LOW` now allows up to 3 words before the low word, and those words may themselves be high words. In `direction()`, `RUPEE_FALLS` is tried before `RUPEE_RISES` and removes the text it matches, so the low reading wins.
  - Evidence (score at the parent → score at HEAD):

    | Headline | Parent | HEAD |
    |---|---|---|
    | Rupee hits 3-week high after lows | 0 | -1 |
    | Rupee hits record high after lows | 0 | -1 |
    | Rupee hits peak after record lows | 0 | -1 |
    | Rupee hits two-week high off lows | 0 | -1 |
    | Rupee hits one-month high from lows | 0 | -1 |
    | Rupee hits back from lowest levels | 0 | -1 |
    | Rupee hits importers with lowest margins | 0 | -1 |

    One case is older: "Rupee hits high from lows" and "Rupee hits strongest since lows of 2023" (one or two words between "hits" and the low word) were already -1 at the parent.
  - Failure scenario: a "Rupee hits 3-week high after lows" headline counts as bad macro news. It can push the market view bearish or trigger a news exit on a held trade. This only affects exits and the news guard (it cannot enlarge a trade), and the headline shape is uncommon. That is why it is minor.
  - Fix:
    - Stop the filler words at the first high or low word. For example, use `(?:\s+(?!(?:highs?|peak|highest|strongest|lows?|lowest|weakest)\b)(?:an?\s+)?[\w-]+){0,3}` in both `RUPEE_HITS_LOW` and `RUPEE_HITS_HIGH`. Or score whichever of `RUPEE_FALLS` and `RUPEE_RISES` matches earlier in the headline.
    - Add "Rupee hits 3-week high after lows" (+1) and "Rupee hits peak after record lows" (+1) to the test.
- **Nit (not a finding):** the `_load_reference_if_needed` docstring still says alerts go out "only on a trading day before the close". It should also say "from 08:45". Separately, runner.py now imports `DEFAULT_ACTIVE_FROM` from the news poll schedule; that is acceptable but couples the runner to the news module.

No other regressions in fno/live/runner.py or fno/live/news/classifier.py. Every change in runner.py is limited to `_market_day_ahead` and the problem-alert timestamp. The only classifier change is the one regex.

**Final verdict: PASS.** N18 to N20 are closed. N21 is minor and does not block the wave; I recommend fixing it in the next round.