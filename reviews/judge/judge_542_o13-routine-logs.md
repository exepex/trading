# Judge 542: O13, routine run logs in Drive and the hourly routine watcher (lane 1)

Verdict: **FAIL** at `aa49a433` (`story/o13-routine-logs`, PR 134). There are three must-fixes:
- the watcher never looks past midnight;
- the secret scrub is not pinned where it is used;
- names are checked after the command has already run.

Most of the build is sound. The table and the mutation results below show which parts I verified.

## Claims vs reality
| Claim / orchestrator's check | Reality | Status |
|---|---|---|
| Write-once Drive paths, `AreaStore(owner Drive, "logs/routines")`, `<day>/<routine>/<HHMMSS-token>/` | Met. Every file is a new path. The owner store refuses different bytes on an existing path (`GoogleDriveUploadStore`, verified in judge 242). | met |
| Secrets scrubbed before every put and every alert | Step files, `end.json` notes, Drive error lines and the in-run alert's lines are scrubbed in the code. **But `WATCH_FAILED` sends the exception text unscrubbed. Neither the step file's scrub nor the alert's scrub is tested (both of my mutations survive).** | **not met (must-fix 2)** |
| Exit code passed through | Met for valid names (my mutation is caught). **Not met when a name is invalid (must-fix 3).** | **partly** |
| `flock` on parallel steps | Met. Read-change-write runs under each routine's lock, and removing the `flock` is caught. | met |
| Watcher slot windows, grace and maximum durations against the live times | The start times match the instructions table (section 1). Grace is caught by my mutation. **A routine whose maximum runs past the last check of the day is never called stuck (must-fix 1).** `EARLY_MINUTES` and the schedule times are not pinned (follow-up). | **partly** |
| One alert only, in-run vs watcher | Met. The in-run alert writes `failed_key(routine, run)`, the watcher's FAILED uses the same key, and removing either side is caught. | met |
| Drive failure never stops a routine | Met. `NoDriveStore` without settings, and `_put` reports any error. The watcher with no Drive raises, so it alerts and exits 1. | met |
| 2 MB kept output | Met. `scrub` on 2.0 MB takes 0.2 s (my probe). | met |
| CLAUDE.md and the prompts unchanged until the owner approves | Met. Only a proposal file is included. | met |

## Must-fix
1. **The watcher only ever reads today, so a run that dies late in the day is never flagged.**
   - `findings()` uses `now.date()` alone.
   - participant-oi starts at 17:11 with a maximum of 400 minutes, so it can only become "stuck" at 23:51. The last check of that day is at 23:17, and from 00:17 the watcher reads the new day.
   - My probe: a participant-oi run with `begin.json` and no `end.json` (its session died silently, the exact case the watcher exists for) gives no finding at 23:17 on the 23rd, or at 00:17 or 01:17 on the 24th.
   - The same loss applies to anything left over when GitHub's schedule slips past midnight. The story itself records "hours late, 14-16 Oct".
   - Fix in the design: the watcher also checks the previous IST day until every routine's last start plus its maximum has passed and been checked. Markers are keyed by the run's day, as they already are.
   - Required test: the probe above alerts once after midnight.
2. **The scrub is not pinned where it is used, and one alert is not scrubbed.**
   - Removing `scrub(...)` from the step-file put (`run_log.py`) and from the in-run alert's lines (`cli.py`) both survive all 17 tests. The only scrub test calls `scrub()` directly.
   - `WATCH_FAILED` formats `f"{type(error).__name__}: {error}"` into a #fno-desk line with no scrub. A Drive sign-in error's text is outside this code's control.
   - Secrets in files and chat are a hard line, so this needs tests at the point of use:
     - a command whose output holds a token: the Drive step file and the posted line both show `[removed: ...]`;
     - the watcher's own error line is scrubbed.
3. **Names are checked only after the command has run.**
   - `--step` is checked in `RunFolder.step_file`, and `--routine` in `RunFolder.new`, both after `runner(args.command)`.
   - My probe with `--step Daily_Run -- true`: the command ran, then `ValueError` was raised.
   - So the routine sees a traceback and exit 1 instead of the command's 0. A failing command's own alert and its log are never written.
   - Check both names before running, at argparse or at the top of `cmd_run`, and test that a bad name exits non-zero without running the command.

## Follow-ups (not blocking)
4. **A step that finishes after `end` silently opens a new run.** `open_run` calls `begin` at the step's end time. This can happen with pre-open's `&` part if `end` comes first. The new folder has no `end.json`, so after 45 minutes it is a false "stuck" alert. Refuse or name it rather than open a new run.
5. **The schedule is not pinned.** Moving participant-oi to 07:11 survives, and so does `EARLY_MINUTES = 0`. Pin `ROUTINES` against the instructions table, or keep the times in one source the table quotes.
6. **Exit codes on a signal.** A signal-killed command returns a negative code. `sys.exit(-15)` gives 241, not the shell's 143. It is still non-zero, but it is not the command's code.
7. **A stale state file goes to the wrong day.** On a machine that keeps `work/routine-logs/`, a run never closed yesterday makes today's steps log into yesterday's folder. Cloud routine containers are fresh, so this matters only on local machines. Compare the day.
8. **Unchecked routine names in local paths.** `--routine` is used unchecked in local state and lock file names, for example `../x`. It is covered once must-fix 3 checks names first.

## Project rules
- 8 modules, 619 lines in all, every file under 350.
- One composition root (`fno/routine_logs/wiring.py`). A new class behind `RawFileStore` (`NoDriveStore`).
- Constants are at the top of each module.
- The workflow is read-only (`contents: read`), and `routine-watch` was added to capture-watch.
- No order code.
- The register row is present. The trial merge conflicted only in `docs/WORK_REGISTER.md`; I kept both rows.

## Gates
Trial merge with `origin/main` (28cf227d):
- `pytest -n auto`: 14647 passed, 1 skipped, 16 xfailed.
- `ruff check` and `ruff format --check`: clean.
- `check_imports`: clean.
- `check_numbers`: clean.

## Mutations by the judge (against `tests/routine_logs`, 17 tests)
- **Caught (5 of 9):**
  - exit code forced to 0;
  - `flock` removed;
  - the watcher's marker check removed;
  - grace removed;
  - the in-run marker not written.
- **Survived (4 of 9):**
  - the step-file scrub removed;
  - the alert-line scrub removed;
  - `EARLY_MINUTES = 0`;
  - the participant-oi start moved.
