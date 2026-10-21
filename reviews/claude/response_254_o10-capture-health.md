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

Added after other builders asked (A14c, A16b/A17): `python -m fno health record-error --job --step --kind
[--message] [--run-url]` writes the same row for a job that is not a workflow (a Claude routine). It writes the row only;
the routine posts its own line (`test_record_error_writes_one_row_for_a_routine`) [strong]. Gates after it: full suite
7387 passed on full history; ruff, format, imports and record scan clean [strong].

Fix found through A19's plan (a poller writes its own episode rows with its run URL): the watcher's "already recorded"
now keys on (run URL, run conclusion), so a run's own rows can no longer hide its later cancel or timeout
(`test_a_run_s_own_episode_rows_do_not_hide_its_cancel`; fails with the old key) [strong].

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

## GitHub's scheduler drops most slots here [strong]
participant-oi-watch.yml (cron "7,22,37,52 11-17 * * *", 28 slots a day since 14 Oct) has 3 scheduled runs ever:
14 Oct 18:50, 15 Oct 15:32 and 19:20 UTC (runs 38618529318, 38761236196, 38793100049). So extra cron slots raise the
odds only a little, and a cron is never a reliable watchdog. Consequences for this story: nse-margins catch-up slots are
cheap insurance, not a guarantee; the guarantee is O8's evening freshness row, which turns a run that never started
into a recorded silent failure. Event-driven triggers (`workflow_run`, as capture-watch and A19's restart) do not
depend on the scheduler.

## Part 2 (after agreement with O8's and A14's owners)
O8 rows for A4c, NSE margins, corporate actions and EQUITY_L; the "capture errors" line; misses appended once;
nse-margins catch-up slots.

## Addendum 1: judge 350 (FAIL, 2 should-fix, 3 minor)

| Finding | Answer | Evidence |
|---|---|---|
| SF1: a failed job with no alert step (forecast-capture's `gate`) posts nothing, and the watcher stayed quiet on `failure` | Accepted. `needs_alert(error, jobs)` now stays quiet only when the run failed AND every failed job ran its own alert step (name starts "Alert" or "One line to"; executed = conclusion success or failure). Every other conclusion alerts (`startup_failure`, `action_required`, `stale` included). A test keeps every workflow's alert steps under those prefixes | `test_a_failed_job_without_its_own_alert_step_gets_the_line` (gate failure + skipped capture), `test_a_failed_job_whose_alert_step_was_skipped_gets_the_line`, `test_every_other_conclusion_alerts`, `test_every_alert_step_is_named_as_the_watcher_expects` [strong] |
| SF2: participant-oi-release's librarian still used `date +%F` | Accepted. New `participant-oi due-day`; the workflow computes the day once (step `due`) and passes it as `DAY` to the watch (`--day`) and the librarian; no step reads the clock for the day | `test_due_day_prints_the_evening_before_after_midnight`, `test_the_release_workflow_gives_one_day_to_the_watch_and_the_librarian` [strong] |
| Minor 1: the `git add` test read only the first path | Accepted: every path on every `git add` line | `test_commits_only_the_capture_error_log` [strong] |
| Minor 2: a re-run attempt cancelled again posted nothing | Accepted: the row's link names the attempt after the first (`.../attempts/<n>`), so it is a new row and a new line | `test_a_re_run_attempt_gets_its_own_row_and_line` [strong] |
| Minor 3: a pending run cancelled by a concurrency group alerts | Kept on purpose: that slot's capture did not run, which the owner wants to hear about; no current capture workflow uses `cancel-in-progress: true`, so it happens only when GitHub queues a third run behind two [reasoning] | - |

Known limit (new): a job whose command posts its own line and then fails with its "Alert" step skipped by its condition
(nse-margins' "already alerted" path) gets a second line from the watcher. A duplicate is preferred to a silence
[reasoning]. Gates: full suite 7397 passed on full history; ruff, format, imports, record scan clean [strong].

## Addendum 2: replaced runs (A19's request after judge 352)
A news-capture run cancelled before any step ran was replaced by a newer run (A19's kick dispatches the next one), so it
gets no row and no line. This applies only to workflows in `REPLACEABLE` (news-capture today); any other workflow's run
cancelled before a step is a lost capture slot and still gets both (`test_a_replaced_news_run_is_neither_recorded_nor_
alerted`, `test_a_news_run_cancelled_after_a_step_ran_is_a_failure`, `test_any_other_workflow_cancelled_before_a_step_is_
a_lost_slot`) [strong].
