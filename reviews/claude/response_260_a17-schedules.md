# Response 260: A17 schedules, builder's claims (story/a17-schedules, ddb39853)

Builder: A16b/A17 builder (session 01MBnbVU). Judge: F. Lane 1 (schedules, outside services). Asked by the
orchestrator on 16 Oct 2026 (owner: external data must be up to date every day; audit Part A2).

## What changed
- `.github/workflows/global-cues.yml` (new). `global-cues fill` runs at 04:41 IST (cron 23:11 UTC, the previous UTC
  day) and at 14:11 IST.
  - It commits `research/data/global-cues/` and `research/data/manifests/global-cues/`, even after a failed cue.
  - It posts one #fno-desk line naming the failed or stale cues.
  - A second alert step covers a failure in the job itself.
- `.github/workflows/vix-history.yml` (new). `vix-history fill` and `sweep` run for the previous IST month at 07:11 IST
  every day. The job commits `research/data/vix/` and `research/data/manifests/`, then posts one #fno-desk line if
  either step failed.
- `tests/test_capture_schedules.py` (new, 5 tests).
- Docs: the A17 CLI docstring and both data READMEs now say the jobs are scheduled. A VIX `fill` run by hand stays
  lane 1.

## Claims and evidence
1. **The run times fit the publication times** [strong evidence for the code; the publication times come from the
   sources' own docstrings, some evidence].
   - The 04:41 run comes after the US closes (01:30-02:30 IST) and after the Treasury's file (by about 04:30 IST,
     `treasury_source.py`).
   - The 14:11 run comes after RBI's rate (about 13:00-13:30 IST, `other_sources.py`).
   - Why the order matters: Cboe and Nasdaq are downloaded at most once per IST day (`once_a_day`), and a copy drops
     the US day still running (`final_values`). So the day's first run must come after the US close, or that close
     waits a day.
   - Test: `test_the_cue_runs_come_after_the_overnight_files_and_rbi_s_rate`.
2. **Every `python -m fno` command in both workflows parses with the real parser.**
   - Test: `test_every_fno_command_parses_as_the_runner_calls_it`.
   - Mutation: `sweep` changed to `sweeep` makes it fail, then reverted.
3. **The alert names exactly the failed or stale cues.** A STOPPED run (for example, Drive settings missing) names no
   cue and reads "the run".
   - Test: `test_the_alert_names_each_failed_or_stale_cue_and_only_those`. It runs the step's own bash line over a
     planted output and expects `sp500,brent`.
4. **The VIX job asks for the previous IST month.** Test: `test_the_vix_job_asks_for_the_previous_ist_month` runs the
   step's own line.
5. **Failure records come from O10's `capture-watch.yml`** (story O10, `research/ops/capture_errors.csv`), so no second
   format is built here. O10 must add `global-cues` and `vix-history` to its workflow list. I've told its builder
   (013YJ5gj).
6. **Gates on ddb39853:**
   - `python -m pytest -q -n auto`: 7,360 passed in 231 s;
   - `ruff check fno tests tools`: clean;
   - `python tools/check_imports.py`: clean;
   - the record scan on the commit: clean.

## Known limits (stated, not hidden)
- **GitHub starts this repository's morning crons 4-5 hours late** (14-16 Oct). On such a day, the 04:41 run lands
  after 09:15, and the US cues are first seen after the open. The as-of rule (A17) then marks them late, so they are
  never used as known at 09:15: a value marked late, never a wrong one. Only a runner outside GitHub would remove
  this. I will report the measured start times after a week.
- **Not proven from GitHub's runners yet:** whether Cboe, Nasdaq (`api.nasdaq.com` is known to refuse some cloud
  addresses, reasoning only), EIA, Treasury, RBI, FBIL and NSE's VIX API answer requests from GitHub's runners.
  - The first scheduled or dispatched run after the merge will show it. I'll cite that run's log here.
  - A refusal fails the run with one line naming the cue, so it cannot pass silently.
- **A15 has no daily OHLC append.** The design only fetches ended months (`months_to_fetch`), and the daily VIX close
  already comes from index-closes.yml. Daily OHLC rows would need a new story with a new source.
- **A16b's daily catch-up is not scheduled here.** It needs a Groww key, and the owner decided on 13 Oct (DESK_DECISIONS
  rows 60 and 206) never to put a broker key in GitHub. The options went to the orchestrator for the owner.

## Addendum 1: judge 351 (FAIL, 1 should-fix), fixed

I checked each point before fixing it.
- **SF1, accepted.** A step whose `if:` holds no status function gets an implicit `success() &&`. So after the commit
  step failed, the cue-alert step was skipped, and the job-failure step required fill (and sweep) to be `success`. A
  failed cue plus a failed push therefore posted nothing.
  - Fix: one alert step per workflow, the last step:
    - global-cues: `if: ${{ !cancelled() && (steps.fill.outcome != 'success' || failure()) }}`;
    - vix-history: the same, with sweep added.
  - Cancelled and timed-out runs stay O10's to post, so nothing is posted twice.
  - Its line names the failed or stale cues and a commit step that did not succeed. The VIX line gives each step's
    outcome.
  - Tests:
    - `test_the_alert_fires_on_any_failed_step_and_a_failed_commit_and_never_on_a_clean_or_cancelled_run` evaluates
      the step's own `if:` for clean, failed-step, failed-commit, skipped and cancelled runs. It also asserts there is
      exactly one sending step, that it is the last step, and that it ends with `exit 1`.
    - Mutations: putting back the old `if:` fails it, and removing the alert step fails 2 tests.
- **Minor 1, accepted.** `checks FAILED (...)` is now named `checks` (test case added).
- **Minor 2, accepted.** YAML ends an unquoted step name at " #", so the alert steps' names are now quoted.
- **Minor 3, accepted.** The push is retried 3 times (pull, push, 10 s and 20 s waits). A push that still fails is
  alerted through SF1's step.
- **Merge order, noted.** If this merges after O10, I add `global-cues` and `vix-history` to capture-watch's list
  in the merge.
- **For the owner, agreed.** With the measured delays (4 h 40 min to 5 h 01 min), the 04:41 IST run usually lands at
  about 09:20-09:40 IST, so the US cues will mostly be marked late at the open. That is a GitHub limit, and this
  story cannot remove it. A run earlier than 04:41 would come before the Treasury's file (about 04:30 IST).
- **Gates on the fix commit:** 7,715 passed (-n auto); ruff and the import check are clean.

## Addendum 2: main US-cue run at 03:41 IST (orchestrator, 16 Oct)

- **The schedule is now three runs.**
  - 03:41 IST (cron 22:11 UTC): the main run. It lands at 08:41 even if it starts 5 hours late. It comes 71 minutes
    after the winter US close (16:00 New York = 02:30 IST) and 131 minutes after the summer one (01:30 IST).
  - 04:41 IST: the backup for the Treasury's 10-year yield, published by about 04:30 IST (`treasury_source.py`). That
    cue is downloaded on every run, so an on-time 03:41 run that came before the file is completed before the open.
  - 14:11 IST: RBI's reference rate.
  - The test now asserts:
    - main run after 02:30 IST;
    - main run plus 5 hours before 09:15;
    - backup between 04:30 and 09:15;
    - afternoon run between 13:30 and 19:00.
- **When Cboe and Nasdaq are final: reasoning only, not measured.**
  - I tried to measure it with Cboe's `Last-Modified` header. At 11:44 UTC it read 11:09 UTC, long after the close, so
    the file is regenerated on a timer, and the header shows nothing about when the close lands.
  - Cboe's quotes are 15-minute delayed, so the close should be in the file by about 16:20 New York. Nasdaq's history
    API has no stated time.
- **Why the 04:41 run cannot back up the US closes.** The owner's once-a-day condition means the first copy of an IST
  day is the day's only one, and the 04:41 run reuses it. So if an on-time 03:41 copy lacks the close, that close is
  first seen the next day and marked late. It is never wrong, and it is visible in the snapshot log.
- **Measurement promised.** After a week of runs, I'll compare each US close's first-seen time with its run's start
  time and report whether 03:41 ever came too early.
- **On `always()`.** I used `!cancelled()` rather than `always()`: it is the same except on a cancelled or timed-out
  run, which O10's capture-watch posts, so `always()` would post twice.
- **Gates:** 7,715 passed (-n auto); ruff and imports are clean.
