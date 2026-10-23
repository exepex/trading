# Judge 523: MS-P1j follow-up, the instructor wired into the fleet (second judge)

**Scope:** story/ms-p1j-ins-wiring at 4f5f8297 (builder session_01CmKJ6taCLzfEGg7wt6RC4N): its own commits eb5ec57a,
bcf9ab21 and 4f5f8297. The branch also carries an older, pre-rebase state of MS-INS part e (63cabe67), which is mine
under judge 522 (FAIL) and not judged here. Lane 1, second judge; I wrote this without reading Judge B's 507.12.
Round 1 of 2. Judge K (session_019ZApRwkUiNMKDsf1k4W44z).

**Verdict: FAIL.** 1 should-fix, 2 minor, and a merge condition.

## Checked
- `after_outcomes` runs after the outcomes and drift seals and before the counts' write, and again on the rerun fast
  path (`runner.py`, eb5ec57a). A replay passes `no_step`. `IsolatedSessionStep` turns a failure or a time-out into
  one alert by class, never a stop.
- `SessionFilesCommitter` commits only the session's three counts files plus the record root's
  `instructor_counts_path(session)`. A replay's `FleetStores` names no extra, and `.gitignore` ignores
  `research/school/counts/**/.*.part`.
- `SealedDayInputs.why` carries part e's lines (no contract or price; part e's own privacy tests).

## Findings
1. **Should-fix: a timed-out instructor can still race the school's own counts commit in git.**
   - After 300 s `isolated` returns, but the worker thread keeps running (`fleet/isolate.py` says so).
   - The instructor's write path ends in `GitReceiptPublisher.publish`: `recorder.commit` (git add, commit, pull,
     push), then `git fetch`/`log` in the same repository.
   - Meanwhile the main thread goes straight on to `counts.write` and `SessionFilesCommitter.commit` (git add, commit,
     push).
   - Two git writers in one checkout can collide on `.git/index.lock` or interleave a pull. That makes the school's
     own counts commit fail: exactly what "can never stop the school's record" rules out. [reasoning only: the code
     path is direct; I did not force the race.]
   - Expected, one of:
     - the instructor run in a child process, ended at the limit;
     - the step not committing inside the thread (its receipts committed by the main thread after it returns);
     - the counts commit waiting for, or serialising with, any git work the step left running.
   - A test with a step that sleeps past the limit and then commits.

**Minor:**
- (a) `UnfilledEntries._fired` reads each decisions file without catching `StaleSeal`. A damaged file stops the
  instructor's comparison instead of listing the session (part e's `sealed_decisions` lists it as unsealed).
- (b) `build_unfilled_entries` builds the whole record fleet to reach three stores. On `main`, `build_fleet` now
  returns `SwitchedOff` when the school is off, which has no `dashcam` or `books`. Build the stores directly.

## Merge condition
This branch depends on MS-INS part e, which failed judge 522 and will change in round 2. Rebase onto part e's passed
tip and current `main` (the switch now lives in `build_fleet`, with the card check beside it). I will judge that tip
as round 2 together with part e's.

## Plants
None planted this round: the branch sits on part e's pre-rebase base, and the rebased tip is what merges.
