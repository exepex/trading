# Response 153: story O8, the daily health check (story text for the judge)

The story is `docs/stories/O8-health-check.md`, on branch `story/o8-health-check`. The orchestrator gave a go for the
story text only (noise-and-fairness step 6, 15 Oct 2026). No code is written yet.

## Sources read
- Handover, section 11 (`conversations/2026-10-15_handover_noise_fairness.md`).
- Response 144, items 6 and 18.
- The owner's v4 timeline row in `docs/DESK_DECISIONS.md`.
- Every job's committed output on `main`. File and line evidence is in the story's table.

## Choices for the judge to check (reasoning only unless marked)

1. **The window is "last N sessions", not "today".** This answers the cron-lateness trap in the simplest way: every
   run, early or hours late, re-checks the same 5 sessions, and evening jobs that are not due yet are listed as
   `not due`. N = 5 fits GitHub's one-week activity log (some evidence: the log's `time_period=week` in
   `fno/ai/receipts.py`).
2. **Push times reuse F1's `PushReceipts`.** No second GitHub client is written. The commit that added a file comes
   from `git log --diff-filter=A`.
3. **Deadlines are imported from their owners.** One exception: the 15:13 canonical pull lives only in
   `forecast-capture.yml`, so it is a named constant here until step 5's timing-consistency test.
4. **Blank forecast probabilities are reported, not failed.** Whether a blank counts is the forecast protocol's rule
   (G9). The health check reports that the rows exist and are on time.
5. **The watcher of the watcher is the next run, using `research/ops/health_runs.csv`.** A job that never runs at all
   is caught only by the missing 18:00 message (Known limits).
6. **The cron is 17:51 IST, not 18:00.** This is a jittered minute, per the scheduling guidance. A late start is
   harmless (choice 1).

## Facts found while measuring (strong evidence)
- The NSE recorder's canonicals for 14 and 15 Oct both hold `none`. The first real run would report them as
  `missed (none)`.
- `journal/runs/` and `research/data/intraday/slots/` do not exist on `main`: the desk run and A16's marks are not live.
  Their checks start at a `live_from` date set by the orchestrator.
- `forecast-scores.yml` writes reports on some days only. `nse-margins.yml` is not scheduled. Both are left out, with
  the reasons in the story.

## Questions for the orchestrator
1. The response number 153 is my pick, because 150-152 exist on other branches. Please confirm or reassign it.
2. The `live_from` dates for the desk run and A16: should they be the first live day of each, set when that goes live?

## Addendum 1: judge 164 (FAIL on 2f3f777, text only). All ten findings checked and accepted.

| Finding | My check | Change in the story |
|---|---|---|
| SF1: deadline ownership | **True.** `fno/ai/timing.py` holds `LATEST_START = time(15, 13)`, so my "no module owns 15:13" was wrong. A8 23:30, closes 12:00, panel 13:00 and flows 23:59 exist only as cron comments. | 15:13 is imported from `LATEST_START`. The four others are health-owned constants (`A8_RELEASE_BY`, `INDEX_CLOSE_BY`, `PANEL_DAY_BY`, `FLOWS_BY`), each with its cron source, listed for step 5. Criterion 3 greps that they are the only time literals in `fno/health/`. |
| SF2: N = 5 versus the 7-day log | **True by reasoning.** Five sessions span more than 7 days in any holiday week. The judge measured 86 of the 2025 runs; I did not re-run that count. | Accepted the judge's suggestion: the window is the sessions dated from 6 days before the run's IST date up to that date. The oldest push it can need is at most 6 d 8 h 47 min old, so it stays inside the log on every run. Criterion 1 adds the 2025 check: no push older than 7 days. |
| SF3: criterion 1 contradicts the window | **True.** A 03:10 run on a session day moves the window. | The window is defined once. Criterion 1 now requires that session D is checked by every run from D 17:51 to D+6 23:59 and not after. |
| SF4: which time decides "late" | **True.** Forecasts and the desk use in-file times, by their own protocols. | The table has a "time that decides late" column for each row. Criteria 2 and 4 are per row. |
| SF5: one line per (check, session) | **True.** NSE alone would repeat for 5 days. | One line per check, listing its bad sessions. |
| Minor 1: a stopped AI book | **True** (`fire.py:55-65`). | The fire log's reason is shown. |
| Minor 2: NSE label | **True.** The owner moved NSE into the 14:33 routine (conversation of 15 Oct). | The label is "in the 14:33 routine; the Actions job at 14:20 is a fallback". |
| Minor 3: watcher bounds | **True.** | Missing days are reported only inside the window and after the file's first row. Criterion 6 says what a same-day re-run does. |
| Minor 4: "closed day" | **True.** Closed days never enter a window of sessions. | `not expected` is only muhurat, before `live_from`, or the desk's `skipped` step. The closed-day column is dropped. |
| Minor 5: A16 has no deadline | **True.** | It says A16's own per-mark status is final and is reported as counts. |
| Note: F1's 10-page cap | Accepted. | Added to Known limits. |

## Addendum 2: the code (the text passed judge 164 addendum 1 at bf2e2820)

The code is on branch `story/o8-health-check`, lane 1. It adds a new workflow. The schedule exists only on this branch;
nothing was scheduled or changed on `main`.

### What was built
- **`fno/health/`** (12 files, at most 80 lines each):
  - `model.py`: `Deadline`, `CheckResult`, the `SessionCheck` interface, and `judged`/`absent`.
  - `evidence.py`: the repository files and GitHub push times. It uses F1's `PushReceipts`, plus `HealthHistory`
    (git's pickaxe for a row, with `--since`).
  - The checks, one class per evidence kind: `quote_checks.py`, `forecast_checks.py`, `desk_checks.py`,
    `data_checks.py`.
  - `expectations.py`: the one table.
  - `window.py`: the window, defined once.
  - `checker.py`, `report.py`, `run_record.py`, `cli.py`, and `wiring.py` (the composition root, now listed in
    CLAUDE.md).
- **`.github/workflows/health-check.yml`**: cron `21 12 * * *` (17:51 IST), plus a manual run, and a full-history
  checkout. The tokens are given to the check step only, and the job commits only `research/ops/health_runs.csv`.
- **Settings and constants:** `config.yaml` has `health.window_days: 6`, an allowed key in `fno/config.py`.
  `fno/constants.py` has the status names and `HEALTH_RUNS_FILE`.
- **The CLI:** `python -m fno health check [--at] [--dry-run]`.

### Criteria, code and tests (strong evidence: each test run, and each criterion broken on purpose)

| # | Code | Tests (`tests/health/`) |
|---|---|---|
| 1 | `window.py`; `checker.py` `run`; `Expectation.expected_on` | `test_window.py`: D is in the window at 17:51, 23:40, D+1 03:10 and D+6 23:59, and out at D+7. Over every run of 2025 with the real calendar, the oldest needed push is more than 6 days and less than 7 days old. Closed days never appear; muhurat days do. `test_checker_and_report.py`: muhurat days and `live_from` |
| 2 | the four `*_checks.py` files | `test_quote_and_forecast_checks.py` and `test_desk_and_data_checks.py`. Every row has ok, late (1 s past the deadline), exactly-at-deadline ok, each miss case, not due, and unknown. A not-fired book shows its reason |
| 3 | `expectations.py` | Row count 20, and 24 with an added question. `LATEST_START` and `GENERATION_DEADLINE` are the owners' objects. The desk deadline follows `config.yaml`. A test greps that the four health-owned deadlines are the only `time(` literals in `fno/health/` |
| 4 | `evidence.py`, `quote_checks.py` | A commit made at 14:56 and pushed at 16:00 is late. A grep finds no commit-date format or field in `fno/health/` |
| 5 | `report.py`, `cli.py` | All ok is one line. A problem takes one line per check, with same-reason sessions grouped. A broken check posts FAILED and exits 1. A dry run posts nothing. With no token, it says so. A Slack refusal exits 1 |
| 6 | `run_record.py`, `cli.py` | One row per run, a failed run included. Missing days are reported only inside the window and after the first row. A same-day re-run adds nothing new |
| 7 | the workflow | The cron, dispatch, permissions, `fetch-depth: 0`, that the job commits only the run record, and the step-scoped secrets |
| 8 | the real sample below | |
| 9 | the `SessionCheck` interface and `wiring.py` | `tests/test_code_size.py` |

### One deviation from the passed text, with evidence: FII/DII's deadline is 12:00 the next day, not 23:59
Times are from the commits that first added each session's row (`git log -S`, commit time in IST; push time is about
the same):
- participant OI: 13 Oct at 21:50, 14 Oct at 21:28, 15 Oct at 21:14;
- index closes: 13 Oct at 22:59, 14 Oct at 01:11 the next day;
- panel: 13 Oct at 03:27 the next day, 14 Oct at 01:40 the next day;
- **flows: 13 Oct at 09:37 the next day (the market publish), 14 Oct at 01:11 the next day.**

With 23:59, flows would be "late" every day in normal running: that is GitHub's measured lateness, not a stopped job. So
`FLOWS_BY` is 12:00 the next day, the same as the closes. The story's table states this. The other three deadlines are
met on all the measured days.

### Deliberate breaks (quality rule 4): 31 of 31 caught
Each break was run with `PYTHONDONTWRITEBYTECODE=1`, `__pycache__` cleared, and the file restored afterwards. The script
is `breaks_o8.py` in the session scratchpad. Each break was caught by a failing test:
- **Criterion 1:** window one day short; muhurat expected for the 3 pm jobs; `live_from` ignored.
- **Criterion 2:**
  - deadline exclusive instead of inclusive;
  - `none` canonical accepted; incomplete sidecar accepted;
  - an absent file always missed (never "not due");
  - row count not checked; duplicate rows accepted;
  - fire-log reason dropped; reveal not checked;
  - desk's missing steps ignored; skipped run counted;
  - late marks counted as missed;
  - panel status ignored;
  - unknown turned into ok;
  - a malformed file crashing the run.
- **Criterion 3:** forecast count hard-coded to 20; 15:13 typed again.
- **Criterion 4:** push time replaced by an in-file time.
- **Criterion 5:** one line per session; FAILED not posted; dry run posts; a Slack refusal stays green; an `--at`
  without offset not read as IST.
- **Criterion 6:** the watcher ignores the first row; no run row appended; a failed run not recorded.
- **Criterion 7:** shallow clone; `git add -A`; tokens visible to every step.

The first run had one invalid break ("FAILED not posted" left an empty `if` block, a syntax error). It was redone as a
real change, and that version is caught.

### Review agent (quality rule 3)
The agent found no blocking issue. It confirmed by running them that the window edges, the deadline boundary, the
pickaxe on the real rows of 14 Oct, the receipt lookup and the commit step are correct. Its 8 findings:
1. **A failed run wrote no row, so later runs reported "did not run": real, fixed.** A failed run now appends a
   `health check FAILED: <type>` row. There is a test and a break.
2. **A failed Slack post still exited 0: real, fixed.** The run now exits 1 unless the post was sent, so a revoked
   token turns the job red. There is a test and a break.
3. **`--at` without an offset crashed: fixed.** It is read as IST. Test and break.
4. **A malformed file crashed the whole run: partly accepted, fixed in the checker.** A wrong-shaped value
   (`ValueError`, `TypeError`, `KeyError`, `AttributeError`) inside one check becomes that check's `unknown`, so it
   never hides the other checks. Any other error still posts FAILED. The run record's own bad date is not handled: it
   is our own file, so that case is not realistic.
5. **Duplicate forecast rows passed: fixed.** The check counts distinct (forecaster, question) pairs. Test and break.
6. **From 1 Jan 2027 without 2027 calendar rows, every run posts "FAILED: CalendarError": accepted as a known limit.**
   It is loud, not silent, and the 3 pm recorder alerts on the same missing year.
7. **Push race and token scope: partly fixed.**
   - The push race is a known limit. It is the same single pull-then-push as every other job; a lost row shows up the
     next day as "did not run".
   - Token scope is fixed: the tokens go to the check step only. Test and break.
8. **Small points:**
   - The late detail now shows the deadline's date ("due 15 Oct 15:13").
   - Criterion 5's "all ok is one line" holds when nothing is pending. At 17:51 the evening jobs add the "not due yet"
     line, which is the story's own format. My reading only, no evidence.
   - A missing forecast file is `not due` until 15:30, the collection end. This is harmless at 17:51.

### Real output sample (quality rule 6)
How it was made:
- `python -m fno health check --dry-run --at 2026-10-15T23:30:00`, on the real repository at this branch, with
  `FNO_SLACK_BOT_TOKEN` and `GITHUB_TOKEN` unset.
- The dry run posted nothing and recorded nothing.
- With no token, GitHub's activity log answers HTTP 403, so every push-receipt check is `unknown`. The workflow passes
  the run's own `GITHUB_TOKEN`, as F1's capture does.

```
health 15 Oct: 9 problems (9 checks, sessions 9 Oct to 15 Oct)
- 3 pm Groww recorder: unknown (push time unknown: access refused: HTTP 403 from GitHub's activity log) 14 Oct, 15 Oct
- NSE recorder: missed (none) 14 Oct, 15 Oct
- Forecast v2 records: late (last generated 14 Oct 19:27:39, due 14 Oct 15:15; 5 of 20 blank) 14 Oct
- Book 2 sealed forecast: unknown (push time unknown: access refused: HTTP 403 from GitHub's activity log) 15 Oct
- Book 3 sealed forecast: unknown (push time unknown: access refused: HTTP 403 from GitHub's activity log) 15 Oct
- A8 participant OI: unknown (push time unknown: access refused: HTTP 403 from GitHub's activity log) 13 Oct, 14 Oct, 15 Oct
- Index closes: unknown (push time unknown: access refused: HTTP 403 from GitHub's activity log) 13 Oct, 14 Oct
- NIFTY panel day: unknown (push time unknown: access refused: HTTP 403 from GitHub's activity log) 13 Oct, 14 Oct
- FII/DII flows: unknown (push time unknown: access refused: HTTP 403 from GitHub's activity log) 13 Oct, 14 Oct
not due yet: Index closes 15 Oct, NIFTY panel day 15 Oct, FII/DII flows 15 Oct
```

The two real findings are correct against the files:
- **NSE canonicals:** both 14 and 15 Oct hold `none`.
- **14 Oct's forecast records:** last generated at 19:27:39, the capture that ran 4 h late (decision row "The owner
  moves the live forecast capture", 15 Oct).

15 Oct's records show `ok` in the table: last generated at 15:10:09, with 10 of 20 probabilities blank. The desk run and
A16's marks are silent, because they are not live yet.

### Known limits (added to the story's)
- The push race, as in every job.
- The 2027 calendar rows (a loud FAILED until they are added).
- The first real run's push-receipt lines can only be verified in Actions, because this session has no GitHub token.

## Addendum 3: O8b, the NSE calendar's horizon line (orchestrator's go, 16 Oct 2026; for judge D)

The story text is the O8b section of `docs/stories/O8-health-check.md`. Because the story is small, its text and code
are on one branch, `story/o8b-calendar-horizon`.

**A correction to my own message (16 Oct).** I told the orchestrator and the A14c builder that the line first fires on
16 Nov. That is wrong. 31 Dec minus 16 Nov is exactly 45 days, which is not "fewer than 45". The line first fires on
**17 Nov** (44 days left). The tests pin both days.

### Code
- `fno/health/horizon.py`, `CalendarHorizon`: `warning(run_day)` has no side effects; `mark()` writes the calendar's
  SHA-256.
- The checker adds the line to `HealthRun.warnings`. The report makes it one problem line.
- The CLI marks only when the post returned `SENT`, the run did not fail, and the run had the line.
- The wiring loads the concrete calendar, for `last` and `calendar_sha256()`. The threshold comes from
  `config.yaml health.calendar_horizon_days: 45`.
- The workflow commits `research/ops/`. A test checks that only the run record and the marker are written there.
- The marker path is a module constant in `horizon.py`, not in `fno/constants.py`, which is at 348 of 350 lines on
  `main`. That follows CLAUDE.md's rule that module-specific names live at the top of their module.

### Criteria and tests (strong evidence: tests run, and each criterion broken on purpose)
| # | Test (`tests/health/test_horizon.py`, unless noted) |
|---|---|
| 1 | `test_the_line_appears_only_when_fewer_than_45_days_are_left` (16 Nov no line; 17 Nov and 31 Dec one line each) |
| 2 | `test_once_marked_the_same_calendar_never_warns_again_and_a_new_calendar_does` |
| 3 | `test_the_marker_is_written_after_slack_accepted_the_warning`, `test_a_refused_post_or_a_dry_run_never_marks...`, `test_a_run_without_a_warning_never_marks` |
| 4 | `test_the_real_settings_and_calendar_warn_for_2027_from_17_november` |
| 5 | `test_the_workflow_checks_out_full_history_and_commits_only_its_run_record` (now `research/ops/`, and only these two writers) |

**Deliberate breaks: 9 of 9 caught.** The breaks:
1. the threshold made inclusive;
2. the marker ignored;
3. the marker never matching;
4. the wrong year asked for;
5. the line missing from the message;
6. the marker written even when the post was refused;
7. the marker never written;
8. the threshold typed in code instead of read from config;
9. the workflow dropping the marker.

### Real sample
`python -m fno health check --dry-run --at 2026-11-17T17:51:00` on this branch, with no tokens. The dry run wrote no
`research/ops/`.

```
- NSE calendar covers only to 31 Dec 2026 (44 days left): add every row of NSE's 2027 holiday circular to research/data/calendar/nse_sessions.csv (source cited); look-ahead jobs such as A14c's stress run stop earlier, and every job that asks the calendar stops on 1 Jan 2027
```

The wording was agreed with the A14c builder (16 Oct), with one part of their proposal declined: their clause "A14c's
stress run stops from about {last - 25 days}" would copy A14c's own look-ahead offset into O8, and the copy would go
stale silently if A14c changed it. A fixed "6 Dec 2026" would be wrong from 2027 on. The line names the consequence
instead, without copying the number. My reasoning only.

The same run reports 9 other problems, all for sessions that have not happened yet.
