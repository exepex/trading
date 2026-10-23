# Story O13: routine run logs in Drive, an immediate failure line, an hourly watcher

**Why (owner, 23 Oct 2026):** "when routines run, we do not know if there is a problem ... I want to redirect routine
trigger logs to Google Drive so that any session in any machine ... could read those logs"; "each routine will have its
own log file for each run ... categorize them by dates"; "some GitHub action that will run every hour that checks if
there is any routine that got failed, find out the root cause, and send a Slack notification ... as quickly as
possible". A routine's own run record lives only in that account's routine sessions; the routine system marks a
run "succeeded" when the session ends, whatever its commands did (23 Oct: the 14:05 desk session "succeeded" at
14:07 while its run went on to 15:40 in the background).

## Design

- **Layout in Drive** (`logs/routines` area, write-once like every Drive file):
  `<IST day>/<routine>/<HHMMSS>-<token>/begin.json`, `steps/<NN>-<step>.log` (one per command: the command, start,
  end, exit code, then its output; the last 2 MB kept), `end.json` (`ok`, or `failed` with the failed steps).
  A run that dies keeps everything written up to that point.
- **Commands** (`python -m fno routine-log`):
  - `begin --routine R` opens the run;
  - `run --routine R --step S -- <command>` runs it with output shown live, writes its step file and, on a non-zero
    exit, posts one #fno-desk line at once (step, exit code, log path, last 12 lines); it exits with the command's
    own code;
  - `end --routine R --note <line>` closes it;
  - `watch` is the hourly check.
- **Secrets:** every log and alert passes through O5's record patterns first (`[removed: <kind>]`); the three F&O
  channel IDs stay.
- **Never stops a routine:** a Drive failure prints "routine log NOT saved to Drive (...)" and the command still runs.
- **Watcher** (`.github/workflows/routine-watch.yml`, hourly at :17): for each routine in
  `fno/routine_logs/schedule.py` due today (NSE's calendar; the monthly sweep on the 1st), every start whose 15-minute
  grace has passed must have a run: none is **missing**; no `end.json` after its maximum duration is **stuck** (last
  step and its last lines named); `failed` names the step and its last lines. Each finding is alerted once (marker in
  `<day>/_alerts/`); the in-run alert writes the same marker, so a failure is never posted twice.
- **Limits (stated):** GitHub's schedule can start hours late (14-16 Oct), so the watcher is the safety net and the
  in-run line is the fast path. The watcher sees only what the routines logged: a routine that failed before
  `begin` shows as missing, its session record stays in the routine system (claude.ai/code/routines).
  The stock tool's (market-brief) routines are not covered: that repository is read-only for this one.

## Routine instructions (owner's approval needed before any change)

The CLAUDE.md routine sections and the API-created prompts get `begin` after setup, `routine-log run` around each
command and `end` last. Proposed text: `docs/stories/O13-routine-instructions.md`; nothing changes before the owner
confirms it, including each routine's time.

## Claims

1. Code in `fno/routine_logs/` (8 modules, all under 350 lines), CLI registered in `fno/cli.py`, state folder
   `work/routine-logs/` git-ignored.
2. Tests `tests/routine_logs/` (17; also: the last step closes the run, parallel steps all counted): layout, failed run, Drive failure never stops, secrets removed and channels kept,
   live pass-through and exit codes, immediate alert with marker, watcher missing / ok / failed / stuck / hourly slots /
   closed and monthly days / once-only alerts / unsent retried.
3. `routine-watch` is added to O10's capture-watch list (its own failure alerts too).
4. Gates: full suite, ruff, check_imports (results in the handover to the judge).

## Round 2 (judge 542 FAIL at aa49a433): what changed

Every must-fix was checked against the code before it was fixed. All three are correct.
1. **The watcher reads yesterday too** (`watch.py` `findings`). A run that dies late (participant-oi: its 400
   minutes end at 23:52, after the last check at 23:17) or a check GitHub delays past midnight is still found. Each
   alert marker is keyed by the day of the expected start (`Finding.day`), so it is alerted once. The in-run marker
   takes the run's own day from its path. Test: `test_a_late_run_that_died_is_alerted_once_after_midnight`.
2. **Scrub pinned where it is used.** The watcher's own error line is now scrubbed. Tests cover a token in a command's
   output (the Drive step file and the #fno-desk line) and in the watcher's error line.
3. **Names are checked before anything runs.** `--routine` and `--step` use `type=name_argument`: a bad name exits 2
   at argument parsing and the command never starts. This also covers follow-up 8 (`../x`). Test:
   `test_a_bad_name_stops_before_the_command_runs`.

Follow-ups, also done:
4. A step with no open run (`begin` missing, or the pre-open background part ending after `end`) is its own run,
   closed at once with a note, never a false "stuck". `end` with no open run writes nothing: an empty "ok" run would
   hide a failed one. The watcher now checks every run in a slot, not only the last.
5. `ROUTINES` is pinned to the live times (`test_the_schedule_matches_the_live_routines`). The 10-minute early edge
   is pinned too.
6. A signal-killed command exits 128 + n, the shell's code.
7. A state file left open for more than a day is not reused. A run crossing midnight keeps its steps.

Tests: 29 in `tests/routine_logs/`. The judge's 4 surviving mutations and 4 more (today-only watcher, watcher-error
scrub, signal code, orphan run left open) are each caught.
