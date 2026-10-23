# Story O1-day-lock: one daily run per day, and a wait that says it is a wait

Owner: the O1/O2 builder (session_014zYLf18PgCzR7YoHs1X5Dp). Lane 1, judge D: the scheduled routine and Drive
writes. It comes from the A4h builder's finding (session_01MKtUHByHsR9cNwaP5KhFYH, 23 Oct 2026).

## What happened (strong evidence: the committed run log, git, and the A4h builder's read-only Drive listing)

- Friday 23 Oct, run A: `close_read` started at 15:33:23, right after `candles`. It then waited, as designed, for A4h's
  15:40 read (`NotBefore`) and printed nothing.
- The routine session took the silence for a hang. It "stopped" the run and started rerun B at 15:39:42, but A was
  still alive.
- B started its own `close_read`, because a rerun skips only finished steps. Both read NSE at 15:40. Both uploaded
  `data/closes/2026/10/2026-10-23.first.raw.json` to Drive 0.8 s apart: a check-then-create store cannot stop two
  processes.
- Drive now holds two items with that name. Two `close_read` commits followed, six seconds apart: dfbd8c0f and
  ed4caf49 (B's, which then failed with exit 1).
- The committed records cite copy 1. The stray copy has no receipt, and a DriveCache folder sync now raises
  `RawFileConflict`.

## Root cause

- Nothing stopped a second `daily run` of the same day beside a living one. F1's `part_locks` cover only the 3 pm
  parts.
- Nothing told the routine that a long silence was a wait. A4h's wait was 7 minutes, the desk's 14:58 wait after a
  14:11 v4 finish is 47, and both are silent.

## The rule

1. **One run per day per container.** `daily run` holds an exclusive `flock` on `journal/runs/.parts/<day>_run.lock`
   (git-ignored) for its whole life, taken before anything is built.
   - A second run of that day prints "another daily run of <day> is running in this container (since <time>): this
     run did nothing; wait for its last line, never stop it while it prints" and exits 1. No step runs and nothing is
     written.
   - The kernel frees the lock when the holder dies, so a rerun after a crash or a real kill goes on as today.
   - The descriptor is not inherited, so a 3 pm part that outlives its run (F1) never holds the day.
2. **Every wait of a minute or more says so.** `AnnouncedWaiter` wraps the run's waiter and prints "waiting until
   HH:MM IST (the next step's time; not a hang, never stop the run)" before the wait starts. A repeated moment, a past
   moment or a short poll prints nothing.
3. **The routine's text** (CLAUDE.md, daily desk routine, step 2) says the same: a "waiting until" line is a wait, and
   "another daily run" means the first is alive.

## Known limits (said plainly)

- The lock is per container. Two sessions in two containers can still run the same day at once, and only Drive's
  store could stop that. Its check-then-create race is A4h's and O9's store, outside O1. The A4h builder has the
  finding; I name it to the orchestrator.
- The stray Drive copy is the owner's call: a delete in a write-once store. Nothing here touches it.

## Acceptance

1. A second lock of the same day is refused and names the living run's start. The lock is free again after its
   holder ends, and a different day has its own lock.
2. A child started by the run does not keep the day's lock.
3. With the lock held by another process, `daily run` prints the one line, exits 1, builds nothing (the runner
   factory is never called) and writes no run log. Removing the check fails this test (mutation run).
4. A wait of a minute or more prints the line once. Short polls, past moments and a loop towards one moment print
   nothing more. The wait itself is unchanged.
5. The run built by `build_day_runner` waits through `AnnouncedWaiter`.
6. The full suite passes.

## Claims

- Acceptance 1-5: `tests/daily/test_day_lock.py`. Acceptance 3's other process is a real child process holding the
  lock (strong evidence). Mutation: with the CLI's check removed, the test fails.
- `tests/daily/test_steps.py`: the command test passes `root=tmp_path`. My first version wrote the day's lock file
  into the repository, and the repo-data guard caught it in four weather tests' teardowns. Fixed at the root: every
  `cmd_daily_run` caller in the tests now names its root.
- Gates on this branch (based on main): pytest -n auto (FNO_SLACK_BOT_TOKEN unset) passes 14589, with 1 skipped and
  16 xfailed. ruff check, ruff format --check, check_imports, check_records and check_numbers are all clean.
- Not changed: the 3 pm parts' F1 locks, every step's action and time, and the run log.
