# Judge 293: O1 fix, the 3 pm parts' earliest start (story/o1-part-start at 7b08108c)

**Verdict: PASS. Lane 1 (the daily run, anything that decides a trade). Merge before Monday 19 Oct's first live run,
once the full gates pass on the exact pushed tree.**

## The bug, checked
`fno/quotes/recorder.py`: `MAX_EARLY_WAIT_SECONDS = 20 * 60`. A start more than 20 minutes before `WINDOW_START`
(14:55) returns `RecordResult("too early")` and records nothing (lines 137-140). O1 started NIFTY's and NSE's parts as
the run's first step. So any run starting before 14:35 lost both records, which means no pack and no decision. The
routine starts at 14:33, so this is a real path in normal running (strong evidence: the O2 end-to-end day printed
"too early").

## Criteria
| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | NIFTY and NSE never start before A4's limit | MET | `EARLIEST_START` = 14:55 − 20 min + 3 min = 14:38, from A4's own constants (one source); `QuotePart.not_before` |
| 2 | They start once their time has come, from every wait | MET | `start_due()` is called from `start` (the day opens), `service()` (the `ServicingWaiter` and a stopped run's `finish`), and each `CommandStep`'s poll through `waiting` |
| 3 | No git outside the run's thread between steps | MET | `start_due` only starts child processes; commits stay in `service`/`_finish` between steps. The quote-part children run no git (O2's lock premise, judge 204 add. 3, still holds) |
| 4 | A stopped or closed day still records | MET | `_finish_parts` → `finish(waiter.until, fills_by)` services until the parts are done, so a stop at 14:34 starts them at 14:38. A closed day's parts start at 14:38 and print "not a trading day" |
| 5 | The indices part is unchanged | MET | it still starts after NIFTY's commit; its window (15:01) is inside A4's limit |
| 6 | Gates on a trial merge with main | MET | 7809 passed, 15 xfailed; ruff and check_imports clean |

## Planted mutations (all reverted)
| Mutation | Caught |
|---|---|
| Margin −3 min (earliest start 14:32, outside A4's limit) | yes, 4 failed |
| `service()` no longer starts due parts | yes, 19 failed |
| `not_before` ignored | yes, 2 failed |
| A command's wait no longer starts due parts | yes, 1 failed |

## Notes (not should-fix)
1. **A long in-process step running across 14:38 delays the parts' start until it returns.** The desk's in-process
   steps before the pack are short (download, history fetch at most 120 s), and starting late is safe while the parts'
   own window (14:55-15:10) lasts, so I see no path to a loss.
2. **A closed day's run now ends at about 14:38, not at once**, because its parts start at 14:38 to print "not a
   trading day". That costs about 5 minutes of routine time on closed days.
3. Monday 19 Oct's run log should show NIFTY and NSE started at about 14:38. I will check it with O1 criterion 9.
