# Judge 569: O1's DRY2 fixes R1 (the indices' early limit) and R2 (one failed step never ends the day)

Judge B, 24 Oct 2026. Story/o1-r1r2-step-safety at e8dc9498d (from main d76c18adf); lane 1, money path. Story:
`docs/stories/O1-daily-run.md`, "Fix after DRY2".

**Verdict: FAIL, round 1 of 2: two should-fixes.** R1 is correct; R2's catch is correct but changes the rerun contract
unstated, and one claimed refusal is untested.

## R1: the indices wait for their own early limit

- **The limit:** `INDEX_EARLIEST_START = earliest_start(INDEX_WINDOW_START)`, 14:44, by the same arithmetic as NIFTY's
  14:38.
- **It now holds for a waiting part:** `start_due` requires both `_waited_for` and `_due`. `next_start` counts a waiting
  part once its predecessor has ended, so the run's waiter wakes at 14:44 when NIFTY ends earlier, and `service` calls
  `start_due` after committing NIFTY.
- **My plants:** the indices given NIFTY's limit (caught); `next_start` ignoring a waiting part (caught).

## R2: an unexpected error fails one step

- **The catch:** `_run_step` re-raises `CommitFailed` and `GitFailed`, so those still stop the run (my plant
  swallowing them fails 8 tests). Any other `Exception` becomes `STEP_FAILED` with its type and one line, plus one
  alert.
- **Downstream reads, checked:**
  - `fills` reads the snapshot's and decisions' logged results, so the `NEEDS` refusal is right.
  - `exits` reviews through its own gate.
  - `decisions` only observes the books' commits, so a failed pack leaves every book late. It never decides on a missing
    pack.
  - `fill` does not read the versions step.
  - A failed exits step makes every book unreviewed the next session, so no book opens anything new.
  - A failed owner-timing step already blocks opens (`_unfilled`).
- **My plant dropping the alert** is caught.

**Gates on e8dc9498d (run by me):** 15,115 passed, 1 skipped, 15 xfailed; ruff, format and check_imports clean. It
merges cleanly with current main.

## SF1 (should-fix): a step failed by an unexpected error is never retried by a same-day rerun, an unstated change

- **Path:**
  - Before R2, an unexpected exception in a step propagated out of `DailyRun.run`, so the step was never recorded and a
    rerun repeated it.
  - Now `_run_step` records it as `STEP_FAILED`. `RunLog.done` is "in the log", and `record` refuses a second record
    ("a run never repeats a step"), so every rerun that day skips it.
- **A normal case:** a transient failure inside `exits`, such as a Drive or HTTP timeout raising from a read the
  review makes. The positions whose exits were due today stay open until the next session's run, and the owner's
  rerun (CLAUDE.md: "A rerun the same day skips the steps already done") cannot recover it.
  - Tomorrow's `_unreviewed` blocks new opens, but the due exits themselves are a day late. On a stop-loss exit that is
    real paper loss.
- **The claims do not say this.** The story's R2 section describes the run going on, not that a failed step is final
  for the day.
- **Test it must pass:** pick one rule and pin it.
  - (a) A rerun after a step failed by an unexpected error runs that step again, with its inputs re-checked and nothing
    doubled, at least for exits.
  - (b) If the owner or orchestrator rules the failure final, the claims say so plainly, and a test pins that a rerun
    leaves it failed, with the alert naming that a rerun will not retry it.
- **Fix (reasoning only):** record unexpected failures so that `done()` does not count them (for example
  `done = step in steps and not failed`), with `record` replacing a failed entry. Exits and fills are already built to
  be rerun safely after a crash.

## SF2 (should-fix, test only): fills' refusal after failed decisions is untested

- **The plant that survives:** `NEEDS = {"fills": ("snapshot",)}`, with decisions dropped, passes `tests/daily`,
  `tests/timetable` and `tests/desk` (357 passed).
- **Why it matters:** the claims state the fills step is refused when either input fails, and fills decides trades.
  `test_step_error_run.py` plants only the snapshot's failure.
- **Test it must pass:** with the decisions step failed by an unexpected error, fills is `refused` naming decisions,
  and no fill is made. The plant must fail it.

## Addendum 1 (pending: round 2 not yet judged)

**Status: PENDING.** The head at the time of writing is f0bb2aa9c. The session is handing over (the orchestrator,
usage at 100%). The next judge finishes round 2 (the last allowed) on the builder's SF1 and SF2 commit.

**Already checked on f0bb2aa9c (holds):**
- **Fail closed:** fills is refused when its input step has not run, as well as when it failed.
- **One rule:** `run_log.problem_steps` and `book_results` give `{}` for a failed or refused step.
- **The scoreboard's `committed_runs`** is guarded. `uncollected()` raised `AttributeError` on a failed decisions step
  (I reproduced it); it now reads no books.
- **The reader list** matches my own map: opening_runs, reviews, health, the scoreboard's runs, snapshot_ids and
  missed, and `_unreviewed` are safe. The card's decisions reader goes in T1d, merged together with R2.

**What remains to check on the next head:**
1. **SF1, under the orchestrator's ruling (24 Oct 06:24):** a step failed by an unexpected error is recorded failed
   and retried on a same-day rerun, while a finished step never repeats.
   - Verify `RunLog.done` and `record`: a failed entry is replaced, and an OK or refused one never is.
   - Verify the builder's table of each desk step as safe or not safe to retry, against the code: in particular,
     whether a retried `fills` or `exits` after a partial write can double a fill, an exit or a ledger row, and how the
     partly written step's commit behaves. A step not safe to retry stays final, with its reason stated.
   - A test: a rerun after a planted exits failure runs exits again, with nothing doubled.
2. **SF2:** with the decisions step failed, fills is refused naming decisions. My plant
   `NEEDS = {"fills": ("snapshot",)}` still passes `tests/daily`, `tests/timetable`, `tests/desk` and
   `tests/scoreboard` on f0bb2aa9c (489 passed). It must fail.
3. **The full gates** on the head, and the merge with main (and with T1d, which merges together).
