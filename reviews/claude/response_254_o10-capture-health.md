# Response 254: story O10, every external capture fresh or loudly failed (builder's claims, part 1)

Builder session_013YJ5gjXdxtFu6mwXP6v48N, branch `story/o10-capture-health`. Story: `docs/stories/O10-capture-health.md`.
Labels: **[strong]** = test, run log or file; **[some]** = partial evidence; **[reasoning]** = judgement only.

## Part 1 (this push): the watcher, the error log, the participant-OI fix

| Criterion | Claim | Evidence |
|---|---|---|
| 1 | A failed, cancelled or timed-out run gives one row (job, first failing step, kind, run URL); the same run twice gives one row; `success`, `skipped`, `neutral` give none | `tests/health/test_capture_failed.py` (fixtures trimmed from real runs 38801338770 and 38745053176) [strong] |
| 2 | One line for `cancelled` and `timed_out`, none for `failure`; without a Slack token the row is kept and the command exits 1 | same file [strong] |
| 3 | A message is one line, at most 200 characters, built from step names only (never a log) | `test_message_is_one_short_line`; `run_failures.py` reads only `name` and `conclusion` [strong] |
| 4 | `capture-watch.yml` watches every workflow except `checks` and itself, `actions: read` + `contents: write`, no concurrency group, commits only the log, no `${{ }}` inside a script | `tests/health/test_capture_watch_workflow.py` [strong] |
| 6 | `participant-oi watch` at 01:52 IST watches the previous day once and returns; at 12:00 and 17:11 it watches today | `tests/research_data/test_release_watch_due_day.py`; with the fix reverted, 2 of its tests fail [strong] |
| 8 | Gates | see "Gates" below |

Real run against GitHub's API (no Slack token, local log reset afterwards) [strong]:
```
$ GITHUB_TOKEN= python -m fno health capture-failed --run-id 38801338770
2026-10-16,participant-oi-release,release / Watch NSE's archive until today's file appears (A8),cancelled,release / Watch NSE's archive until today's file appears (A8): cancelled,https://github.com/exepex/trading/actions/runs/38801338770
alert NOT sent: FNO_SLACK_BOT_TOKEN is not set
exit 1
```

## The four health problems (run evidence)

1. **participant-oi-release cancels [strong].** Runs 4, 6, 8 started 3-4.5 h late (01:51-03:22 IST) and were cancelled
   after exactly 5 h 50 min in the watch step (job 116650851676: step 6 20:22:16Z to 02:12:16Z). Cause: the watch's
   default day was `now_ist().date()`, the next day, so it watched a file not due for 20 hours until the 350-minute
   timeout. Fixed in code (criterion 6). The cancel posted nothing; the watcher now records and posts it.
2. **health-check "never ran" [strong for the dates, open for the run].** Created 15 Oct 18:31 UTC; cron 12:21 UTC; no
   slot existed before 16 Oct 12:21 UTC. The first run will be cited here when it appears.
3. **nse-margins [strong].** The 03:30 IST cron merged 16 Oct 06:08 UTC (3c333417); its first slot is 16 Oct 22:00 UTC.
   On 16 Oct one morning slot started 07:12 UTC and the other never started. Catch-up slots wait for the A14 owner's
   agreement (asked through the orchestrator).
4. **quote-recorder-nse [strong for the cause, some for the cure].** Started 19:34 and 19:12 IST, after the 15:10
   window, so `none` plus an alert. Kept (owner, 15 Oct). Since 16 Oct the routine records NSE first, so a late run
   should print "already recorded" and exit 0; 16 Oct's run will be cited.

## Known limits found while building
- GitHub reports a `continue-on-error` step as `success` (job 116456411518: the record step failed but shows
  `success`), so for such workflows the row names the step that finally failed the run (often the alert step), not the
  first problem. The run URL in the row leads to the log [strong].
- Unquoted YAML step names lose everything after ` #` ("One line to #fno-desk ..." shows as "One line to"), so some
  rows carry a truncated step name. Cosmetic; not changed here (other owners' files) [strong].
- `workflow_run` gives no event for a run GitHub never starts; part 2 (O8's freshness rows) covers that.

## Part 2 (after agreement with O8's and A14's owners)
O8 rows for A4c, NSE margins, corporate actions and EQUITY_L; the "capture errors" line; misses appended once;
nse-margins catch-up slots.
