# Judge 240: O8b, the NSE calendar's horizon (one line, once) and the health job's failure alert

Trading `story/o8b-calendar-horizon` at 3e215fbb (C5/E1b builder 012eM7Ti8ZaSVowgyMkgoGmM; claims: response 153
addendum 3). Story text: "## O8b" at the end of `docs/stories/O8-health-check.md`, text and code on one branch. Lane 1:
Slack output and a workflow. Judge D, 16 Oct 2026.

**FAIL: one should-fix.** The horizon line is right; the new failure alert misses part of what it claims to cover.

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | No line on 16 Nov (45 left), one on 17 Nov (44) and 31 Dec; it asks for next year's rows | MET | Real calendar: `CsvSessionCalendar.last` is 2026-12-31, so 16 Nov has 45 days left and 17 Nov has 44. `left >= days` returns None. **My mutation** `left > days` fails 2 tests. The line names 2027 and the file, and states the consequence without copying A14c's offset. |
| 2 | Same SHA-256 never warns again; a new one does | MET | `_warned` compares the marker with `calendar_sha256()` (tests). |
| 3 | Marked only after Slack accepted | MET | `if sent == SENT and not code and run.warnings`. A dry run has no sender. **My mutation** dropping `sent == SENT` fails 1 test. |
| 4 | Threshold from config | MET | `health.calendar_horizon_days: 45`. |
| 5 | The workflow commits the marker | MET | `git add research/ops/`. Nothing else in the repository writes under `research/ops/` (grep). |
| Scope: failure alert | **PARTLY** | See the finding. |
| Gates | MET | On 3e215fbb: 6961 passed (`-n auto`, Slack token unset), ruff check and format clean, check_imports clean. Trial merge with main is clean, 6972 passed. |

## Finding (should-fix)

**The new alert step is silent for a crash inside the check step that happens before anything is posted.** Its
condition is `failure() && steps.check.outcome != 'failure'`, which assumes that a failed check step always posted
"health check FAILED". It does not:
- `cmd_health`'s `try` starts after `build_alert_sender()` and the imports;
- an import error in `python -m fno` (for example a module on main that needs a package missing from
  `requirements.txt`; ChatGPT and lane-3 jobs push to main directly) fails the check step before `cmd_health` runs.

In both cases the check step fails with nothing posted, and the alert step stays quiet. Response 153 addendum 3 lists
"an import crash" among the failures the new step covers; that claim is not true. This job is the watcher of every
other job, so a silent red run is exactly what A14c's response 239 item 7 asked to close.

**Fix (the builder's choice; one way):** let the check step record that it posted. For example, `cmd_health` writes
`posted=true` to `$GITHUB_OUTPUT` right after `alerts.send` returns, and the alert step uses `if: failure() &&
steps.check.outputs.posted != 'true'`. Add a test for an import-time crash, or a sender that cannot be built, giving
exactly one line.

## Notes

- The workflow header (lines 4 and 15) still says it commits only `research/ops/health_runs.csv`. Update it to name the
  marker, as the step's own comment does.
