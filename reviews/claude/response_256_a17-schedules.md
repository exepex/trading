# Response 256: A17 schedules, builder's claims (story/a17-schedules, ddb39853)

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
