# Response 269: F8c, AI book runs' usage captured every day (branch `story/f8c-usage-capture`)

Builder 0134MoC6 (F8/BG1 owner). Asked by the orchestrator on 16 Oct 2026: the owner wants all external data captured,
nothing lost (gap audit `docs/CORE_ENGINE_GAP_AUDIT.md`, Part B2 item 9). Lane 1: it touches the AI books' routine
steps and an outside service (Slack alerts). For judge B (the orchestrator's choice, 16 Oct 11:21).

## The gap (checked on `main`)

- `accounting/ai_usage.csv` holds one row, and none for the G5 book routines of 14-16 Oct.
- BG1's self-timed record exists (`fno/budget/self_timed.py`), but only a routine's prompt could call it, and the v1
  prompts (frozen by hash) never do. A fired routine's session cannot be read afterwards, so each day's minutes are
  lost.

## Design (agreed with the G11 owner, 013xqaNT, who drops the overlapping round 2a, fa758dcc)

1. The capture sits inside the steps today's prompts already run, so no prompt changes:
   - `brief` notes the run's start in the private working folder (`.ai_book/started.json`, kept from the first brief);
   - `reveal`, after its own publish, publishes `research/forecasts/ai_v1/timing/<YYYY>/<day>_<book>.timing.json`
     in BG1's self-timed shape. This is a publish of its own: a timing failure prints
     "timing NOT published (<why>)" and never costs the reveal.
2. **Session id:** from `CLAUDE_CODE_REMOTE_SESSION_ID`, set in every cloud session. `cse_<id>` is stored as
   `session_<id>`, the name the session tools and the fire logs use; BG1's `session_key` matches the two. The model
   is left empty: nothing in the routine's environment names it.
3. **One file per book (the G11 owner's point, checked):** both books reveal at 15:15:10. Two appends to one ledger
   would race; one file each cannot.
4. **`ai collect`** (the forecast-capture job, about 15:30 IST):
   - it folds every timing file into the ledger, using G11's `BookUsageRecorder`, moved here with its tests and
     credited;
   - it then sends one #fno-desk alert per run fired that day that has no ledger row (`fno/ai/usage_gaps.py`).
5. **The meter:** a fired session without a row already counts as not captured (`capture_coverage.py`, F8
   criterion 7), so the level reads "not known", never a guessed number. No fake "missing" row is written. The alert
   makes the gap seen on the same day.
6. **14-16 Oct: no "missing" rows are written (the orchestrator asked for them; declined with evidence).** The
   meter already lists all six of those runs as not captured. `not_captured(root, "2026-10", ledger, "2026-10-17")`
   on main returns the six fired sessions of 14, 15 and 16 Oct (book2_hybrid and book3_ai each day). A ledger row with
   a run's session id, even with blank minutes, would make `capture_coverage` count that session as captured, since it
   matches on session id. The meter would then report the gap as closed: the opposite of the goal. The gap is recorded
   where the meter reads it: the fire logs against the ledger. The minutes cannot be rebuilt, and none are invented.
7. **"Fired" source (the G11 owner's request):** the alert reads the same fire logs as `collect`
   (`fno/ai/paths.fired_path`, the per-book `fired` flag, through `capture_coverage.fired_sessions`). A book not
   fired (a stop rule, a refused trigger) used no minutes and raises no alert.

## Criteria and tests (`tests/ai/test_run_timing.py`, plus `tests/ai/test_book_session.py`)

| Claim | Test |
|---|---|
| The reveal publishes the run from brief to reveal in BG1's shape, after the reveal, as its own publish | `test_the_reveal_publishes_the_run_from_brief_to_reveal_in_bg1s_shape` |
| The session id is the environment's id under the session tools' name | `test_the_session_id_is_the_environments_remote_id...` |
| No session id, or a failed publish: said, and the reveal stands | `test_a_timing_failure_never_costs_the_reveal`, `test_a_failed_timing_publish_is_said_and_the_reveal_stands` |
| A retried reveal publishes nothing twice | `test_a_rerun_reveal_keeps_the_first_start_and_publishes_the_timing_once` |
| The ledger gets each book's minutes once; a bad file is a refused line | `test_the_ledger_gets_each_books_minutes_once`, `test_a_bad_timing_file_is_a_refused_line...` |
| A fired run not captured is one alert; a captured one, none | `test_a_fired_run_not_captured_is_one_alert_and_a_captured_one_none`, `test_a_day_with_nothing_fired_alerts_nothing` |
| The book side still imports nothing installed | the existing `test_the_book_side_imports_no_installed_library` |

Changed expectation: a full book run now makes three commits (commitment, reveal, timing),
`test_book_session.py:61`.

## Dependencies and open points (honest)

- **Workflow:** `.github/workflows/forecast-capture.yml` commits only `research/forecasts` (line 126). Until it also
  `git add`s `accounting/ai_usage.csv`, the rows `collect` records are not kept. The timing files are committed and
  are recorded by the next run that commits the ledger, so nothing is lost for good. The G11 owner asked 01VK88Lx for
  this one line. I have not changed the workflow, since it is not my file.
- **A rerun of `collect`** the same day sends the not-captured alert again. That is reasoning-only acceptable: a
  rerun is a hand action.
- **A refused seal:** the routine never reaches reveal, so no timing file is written. That run then shows as not
  captured, with an alert, never as zero (the G11 owner's point; reasoning only).
- **Duration:** the timing covers brief to reveal, so a few seconds after the reveal are not counted. The routine
  ends right after it.
- **Second recorder:** the ledger now has two (`fno/budget/usage_ledger.py` docstring updated). A clash is refused
  by git, and recording again is safe.

## Gates

- `python -m pytest -q -n auto`: 7471 passed;
- `ruff check` and `ruff format` clean;
- `python tools/check_imports.py` clean;
- no changed file is named in any `PROTOCOL.md` freeze list (checked by script).

## Addendum 1: judge 276 (PASS with a merge condition), both points met

1. **Merge condition, done in this branch.** `.github/workflows/forecast-capture.yml`'s records commit now also runs
   `git add accounting/ai_usage.csv`, so the rows `ai collect` records are kept on main. This is lane 1 (a workflow
   file), judged with F8c. Only a path is added; the schedule is unchanged. The G11 owner's request to 01VK88Lx for
   the same line is superseded, and I've told them.
2. **The run's start is now kept per day and book** (`.ai_book/started_<day>_<book>.json`). `brief` parses the pointer
   first and then notes the start. Two new tests cover it:
   - `test_a_second_brief_keeps_the_runs_first_start` kills the surviving plant (start() overwriting on every brief);
   - `test_a_reused_container_never_lends_another_days_start` covers a previous day's start file left in a reused
     container.
3. **Found while adding the workflow line, fixed:** the job's "One line to #fno-desk" step posts every `Omenix F&O AI`
   line of `ai.log` again. The not-captured alert text, printed as well as sent, would have reached #fno-desk twice.
   The printed line is now `usage not captured: <book> <day>: <send result>`, which does not repeat the alert's text;
   a test asserts this.
4. **Collect rerun re-alerts:** unchanged and stated (reasoning only: a rerun is a hand action).

Gates on the merged tree (main merged in): 7691 passed; ruff and check_imports clean.
