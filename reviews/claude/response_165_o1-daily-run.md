# Response 165: story O1, one daily run (story text, claims for the judge)

Branch `story/o1-daily-run`. Story text: `docs/stories/O1-daily-run.md`. Lane 1 (schedule, routine prompt, fills,
Slack). Code waits for the text PASS, E2c's merge and the orchestrator's go.

## Claims

1. Nothing calls `fno desk run`, `fno weather capture`, `fno forecast-v4 capture` or `fno card daily --post` on a
   schedule today. **Strong evidence:** grep of `.github/workflows/` and CLAUDE.md, 15 Oct.
2. The data checks REPLAN names already run inside E3 (`DataGate`, C3/C4); O1 adds none. **Strong evidence:**
   `fno/desk/daily_wiring.py`.
3. GitHub's cron started the NSE recorder about 5 hours late on 14 and 15 Oct (canonicals `none`); the owner's Claude
   routine recorded Groww on both days. **Strong evidence:** the canonical files and `conversations/2026-10-15.md`
   line 618.
4. Weather and v4 capture must run before their cutoff (15:00; 14:30 after G10), so they cannot wait for the
   canonical's push. **Strong evidence:** `fno/forecast_v4_rules/capture.py` `cutoff`, `fno/weather/capture.py`.
5. Start: the existing 3 pm Claude routine runs `python -m fno daily run` (decided by the orchestrator on the owner's
   15 Oct words and `docs/DESK_DECISIONS.md` "O6 scope: timed jobs stay on Claude routines", eeac1897). That it is on
   time: **some evidence** (two days); that it stays on time later: **reasoning only**.
6. `daily.live_from` keeps a first live weather record from ending M1's back-fill before the owner or the G6 freeze
   decides. **Strong evidence:** `fno/weather/capture.py` docstring.
7. O1 changes no step's own code; G10's times reach O1 through their owners. **Reasoning only** until the code round.

## Settled with the orchestrator (15 Oct)

- Start: option A (claim 5).
- O1 owns the routine prompt text and the CLAUDE.md section; A4c, G10 and the handover session send their lines
  through the orchestrator.
- E3's snapshot moving to A16's 15:15 mark: a dependency, assigned by the orchestrator after G10 merges.
- The run-log contract with O8 (session 012eM7Ti8ZaSVowgyMkgoGmM): agreed with its three conditions (one tuple the run
  loops over; status rules; constants size).

## Revision 2 (judge 169 FAIL, 4d86a8c1): both should-fixes accepted

Checked against the files before accepting:
- **Should-fix 1, accepted.** A4c's passed CLAUDE.md steps 2-3b (`story/a4c-all-indices`; judge 151 addendum 2 text,
  judge 160 code) run NIFTY and NSE in parallel, the indices after NIFTY's push, and commit per-part paths. My
  revision 1 committed the whole folder, which A4c forbids (strong evidence: the diff of A4c's CLAUDE.md). Fix: the
  `quotes` step starts A4c's three commands as child processes beside E3's steps, each part commits only A4c's paths
  (word for word; A4c's own test checks CLAUDE.md), NIFTY first; `quotes_done` collects them after `exits`.
  I added one design point of my own: every git command of the run goes through one lock. Without it a part's commit
  and an E3 commit in one checkout can collide, and a failed E3 commit stops the desk (decision 44). That a collision
  would happen is **reasoning only**; criterion 4a tests the order.
- **Should-fix 2, accepted with the orchestrator's option.** After E3's `RunStopped` the card does not run, because
  T1's `--post` writes delivery metadata and nothing more may be committed. What the owner loses that day is said in the
  text: the card's forecast block and its Slack witness. The forecasts stay committed with GitHub's receipt, and the
  stop alert names the cause. That loss is a small cost (**reasoning only**). Criteria 2 and 5 cover it, with a test.

## Revision 2 PASS (judge 169 addendum 1, 9f150096): notes accepted

- Note 1 accepted: E3's `GitCommitter` refuses an unpushed commit the run did not make (`_refuse_stray`, decision 51;
  strong evidence: its docstring in `fno/desk/git_sync.py`). The parts commit through that same committer, and a
  Known-limits line covers a part whose push always fails.
- Note 2 accepted: the parts commit by pathspec, and criterion 4a gains a test with another file already staged.

## Code round 1 (parts that do not wait for E2c; the orchestrator's go of 15 Oct)

What is built (`fno/daily/`, wired in `fno/daily/wiring.py`, listed in CLAUDE.md's composition roots):
- `python -m fno daily run [--day]`: E3's `DailyRun` loops over `DAILY_RUN_STEPS` (`fno/constants.py`), with O1's
  steps passed in as `DayStep`s (`fno/desk/daily_ports.py`). E3's tests, which pass no O1 steps, write exactly
  `DESK_RUN_STEPS`.
- `fno desk run` is replaced by `fno daily run`, so there is one command for the day and no dead entry point. E3's
  stop alert now names `fno daily run` as the rerun. The old CLI test is covered by the runner's stop test.
- **Amendment (see the story text): a `book1` step** after `pack`. Nothing called `fno desk book1` either, so Book 1
  would have been "no decision (late)" every day. **Strong evidence:** `fno/books/book1_cli.py` docstring "No routine
  starts them yet".
- **Quote parts** (`quote_parts.py`, `quote_steps.py`):
  - A4c's three commands run as child processes;
  - NIFTY commits first, and the indices start after NIFTY's commit;
  - each part commits `Git.changed(<A4c's pathspecs>)` through E3's `GitCommitter` (judge note 1);
  - a part still running 20 minutes after `quotes_done` starts is stopped, and its files are not committed (they may
    be half-written).
- **"One git at a time" is the run's single thread** (a story-text clarification, above). The parts never run git;
  the run commits them between steps or while it waits (`ServicingWaiter`).
- **Pathspec commits (judge note 2):** `Git.commit_paths` now commits `-- <paths>` and checks only those paths for
  changes. A real-git test commits each part with another file staged.
- **`daily.live_from`** in `config.yaml` (new allowed key `daily`): weather, v4 forecasts and card are all null, so
  they are `not_live` until the owner or the freeze sets a date.

Criteria and tests (`tests/daily/`; strong evidence: they pass, and each was broken once on purpose, see below):

| Criterion | Test |
|---|---|
| 1 order, closed day | `test_a_session_runs_every_step_once_in_the_tuple_s_order`, `test_a_closed_day_records_only_skipped_and_starts_no_part`, `test_the_desk_s_own_steps_are_exactly_its_tuple_in_order` |
| 2 failure, stop | `test_a_failing_o1_step_is_recorded_alerted_once_and_every_later_step_runs` (3 steps x raise/refusal), `test_after_the_desk_s_commit_failure_stop_the_card_never_runs_and_the_parts_still_commit`, `test_a_part_commit_that_fails_is_alerted_with_its_own_paths_and_the_day_goes_on` |
| 3 restart | `test_a_rerun_skips_every_recorded_step_and_restarts_no_part` |
| 4 parts | `test_nifty_and_nse_start_together_the_indices_after_nifty_s_commit_nifty_commits_first`, `test_a_part_running_to_15_13_does_not_move_the_desk_s_steps`, `test_a_hung_part_is_stopped_after_the_limit_and_the_ended_parts_are_committed` |
| 4a one git, pathspec | `test_each_part_commits_only_its_own_files_with_another_file_staged` (real git) |
| 5 card | the stop test above, and order test (card last) |
| 6 not live | `test_before_its_live_date_or_with_none_a_step_is_not_live_and_calls_nothing`, `test_not_live_and_ok_are_never_alerted_a_raise_always_is` |
| 7 O8's tuple | order tests; the O8 swap waits for O8 on main (below) |

Faults planted on purpose, one at a time (each made a test fail, then was reverted):
- NIFTY-first rule removed;
- the pathspec commit removed;
- parts not waited for after a stop;
- the indices starting without waiting for NIFTY.

Not done yet, with the reason:
- the CLAUDE.md "Daily desk routine" section (criterion 8) waits for A4c's merge (16 Oct), so that it carries A4c's
  lines word for word from `main`;
- anything touching the account files waits for E2c;
- the real day (criterion 9) waits for the owner pasting the prompt.

Said plainly:
- `book1`'s commit failure gets two alerts: E5b's own, and O1's "step book1 failed". I accept the duplicate rather
  than risk a missing alert for other failures (reasoning only).
- The refusal status is read from the commands' printed phrase "nothing written:". A test fails if either command
  stops printing it.

### O8 swap (done in the merge of `main` at 5b1f561e; O8 merged first, judge 170)

- `fno/health/desk_checks.py` imports `DAILY_RUN_STEPS`. Its private `DESK_RUN_STEPS` and the test that parsed
  `daily_run.py`'s source are deleted.
- The O8 builder's status rules (b) are built in:
  - a `failed` or `refused` O1 step is a problem (`missed`), shown with its reason;
  - `not_live` counts as neither missed nor a problem;
  - an absent step is missed.
- New tests:
  - `test_the_check_reads_the_daily_run_s_own_tuple`: a desk-only log misses O1's six steps by name;
  - `test_a_failed_or_refused_o1_step_is_a_problem_with_its_reason_not_live_is_not`.
- `fno/constants.py` is at 348 lines after the merge: still under 350, with no squeeze. The next story that adds a
  block there must split a cohesive block out.

### A14c's margin check (agreed with the A14c builder, 15 Oct)

- `margin_check` is the first entry of `DAILY_RUN_STEPS`. It runs `python -m fno margins stress-broker-check`
  (provisional name), which is idempotent: "nothing to check" with exit 0, exit 1 on a Groww failure.
- It commits only `research/data/margins/stress_broker_check.csv`.
- It is `not_live` (`daily.live_from.margin_check: null`) until A14c's code lands. While the command does not exist,
  a live step would fail every day.
- Tests:
  - the order and failure tests now cover `margin_check`;
  - `test_the_wiring_gives_every_o1_step_and_a14c_s_check_runs_first_writing_one_file` checks that the composition
    root gives a step for every name in the tuple.

### Size split (merge of `main`, 15 Oct)

Merging LR1 put `fno/constants.py` at 351 lines, over the 350 limit. Following the agreed rule (split, never squeeze),
the daily-operations block moved out whole into `fno/constants_operations.py`, with an explicit `__all__`:
E3's decisions step name, `DESK_RUN_STEPS`, `DAILY_RUN_STEPS`, O1's step statuses and O8's health statuses.
`fno/constants.py` imports it with one `import *` line (its `__all__` lists the names), so every
`from fno.constants import ...` in the 25 files that use these names keeps working unchanged. `fno/constants.py` is
now at 341 lines.

### Judge 178 (code round 1 PASS, 3a1c1865): notes

1. Tests added (accepted):
   - `test_quotes_or_card_raising_is_recorded_failed_with_one_alert`;
   - `test_a_quote_part_that_exits_non_zero_gets_no_o1_alert_and_the_others_still_commit` (each of the 3 parts);
   - `test_a_failed_nifty_still_starts_the_indices_after_it_and_lets_nse_commit`.
   The behaviour was already right, as the judge's probe showed: these are tests only.
2. Done: the constants split and CLAUDE.md's root list keep LR1's line (sections above). The full suite ran on the
   merged tree.
3. Accepted: O1 merges only after A4c.
4. Declined, with reason. A dead run's part files may be half-written, since a killed recorder can stop mid-file, and
   only the recorder can say whether an attempt is complete. Committing them blind could put a broken sidecar or
   canonical on `main`. This is now a Known-limits line (reasoning only; I did not test a killed recorder).
5. The orchestrator updates the Handover row.

T2/T3 builder (through the orchestrator): the card runs after `decisions` (final at 15:12) and `snapshot` (C3 final at
15:15). That was always the order (strong evidence: the order test); the table now says so.

### E2c merged (main at 8783b0b2): what it means for O1

- `DailyRun` keeps both additions: E2c's `files` (the private records downloaded before any step) and O1's
  `day_steps`. `build_daily_run` passes both, and E2c's `_unreviewed` input to `fills` is kept in the plan.
- O1 needs no account change of its own. Account writes are E2c's `DriveAccountSync` through E3's committer, and they
  run in the run's one thread like every other commit (reasoning only: the single-thread argument above covers them).
- Book 1's child command downloads its own private records (E2c's `cmd_book1`), in its own process, while the run
  waits.
- Test fix: E2c ignores the account files in git, so the real-git pathspec test now stages a tracked file of another
  writer (`research/notes/another_writer.md`) instead of `cash_ledger.csv`.

### Judge 178 addendum 1, note 6 (required by the orchestrator)

- `quotes` is now the first entry of `DAILY_RUN_STEPS`, before `margin_check`. The parts wait for 14:55 themselves,
  so starting them first costs nothing.
- Every `CommandStep` is stopped after `COMMAND_LIMIT_SECONDS` (600) and recorded `failed`; nothing it wrote is
  committed. This covers a hang in any O1 command, not only A14c's.
- Ten minutes keeps a hung `margin_check` (about 14:35) well before the 15:00 weather/v4 cutoff, and a hung `book1`
  (about 14:58) before the 15:12 deadline (reasoning only: real run times are not measured yet).
- Test: `test_a_command_still_running_at_its_limit_is_stopped_and_failed_never_holding_the_day`.

### Judge 178 addendum 3 (PASS at 43943a52): notes 7 and 8, both accepted

- **Note 7, accepted.** The 10-minute limit does not protect the 15:12 deadline for `book1`: the pack can retry
  until 15:10, so `book1` may start then. The docstring and the story text now say so plainly; E3's late rule
  decides that case. **Strong evidence:** `pack_wait_until` 15:10 in `config.yaml`.
- **Note 8, accepted and fixed.** Every child now starts in its own process group (`start_new_session=True`), and
  `stop()` kills the whole group, so a git or Groww call it started dies with it. This also covers the quote part
  stopped at `FINISH_LIMIT`.
- Test: `test_stopping_a_command_kills_what_it_started_too`, with a real grandchild process. Removing
  `start_new_session` was planted once and the test failed.

### Unsent alerts are printed (found while checking M2's question, 15 Oct)

- **Gap:** `AlertSender.send` returns its outcome line, and O1's steps and the desk dropped it. With Slack down or
  `FNO_SLACK_BOT_TOKEN` missing, every alert of the day would have been lost silently. CLAUDE.md's 3 pm rules require
  the routine to post "alert NOT sent" lines with the Slack connector, so the run must print them. **Strong evidence:**
  `fno/alerts/sender.py` returns the outcome; `Alerted` and E3's `_guarded` ignored it.
- **Fix:** `fno/daily/alerts.py`, `ReportedAlerts`, wraps the one sender of the run. Any outcome other than "sent" is
  printed as `alert NOT sent: <reason> | <text>`. `build_daily_run` takes it (a new `alerts` parameter, E3's own
  default unchanged), so the desk's alerts, the quote parts' commit alerts and O1's step alerts all go through it.
- **Tests:** `test_an_alert_slack_did_not_take_is_printed_for_the_connector_one_it_took_is_not` and
  `test_the_desk_and_o1_share_that_one_sender`.

### Judge 178 addendum 6, should-fix 9: accepted and fixed

- **Accepted, checked.** Every child writes to a temporary file, and the run kept only its last 10 lines. So a
  child's own "alert NOT sent" line never reached the routine: the recorder's alerts, E5b's "NOT committed", the
  card's outcome, and later the margin check, weather and v4 steps. CLAUDE.md steps 3-4 rely on that line.
  **Strong evidence:** `fno/daily/processes.py` before the fix.
- **Fix:** `ChildProcess` reads a child's whole output once, when it ends or is stopped, and prints every line
  containing "alert NOT sent" as written (`UNSENT`, from the sender's own `NOT_SENT`). The run log still keeps the
  last 10 lines.
- **Tests:** a real child printing the line among 14, and a stopped child.
- **Faults planted:** removing the report loop failed 2 tests; skipping the read on stop failed 1.

### Judge 178 addendum 7, should-fix 9(b): accepted and fixed (with 9(a) above, one head)

- **Accepted, checked.** Two senders inside the run built their own `build_alert_sender()`, bypassing
  `ReportedAlerts`: `build_exit_desk` (`fno/desk/wiring.py`) and `build_book1_exit_rules`
  (`fno/books/book1_wiring.py`). Both carry exit alerts. **Strong evidence:** a grep of every `build_alert_sender()`
  in `fno/`. The other hits are outside the run's process: `build_data_gate` is not used by the daily run, and Book
  1's decider runs in its own child, whose lines are relayed by 9(a).
- **Fix:** both take `alerts=None`, so their other callers keep today's sender. The daily run passes its one
  `ReportedAlerts`.
- **Test:** `test_every_sender_inside_the_built_run_is_its_one_reported_sender` builds the real run, walks its object
  graph, and requires every held sender (12 places) to be the one `ReportedAlerts`. Each bypass was put back once,
  and the test failed on its assertion each time.

### The whole git history before the day (asked by E8, 16 Oct)

- **Why:** a cloud checkout is shallow (this session's was 50 commits). Older commits then read as made at the
  boundary commit, and E8's seals and E3's committed decisions are dated by commit time. **Strong evidence:** E8
  builder's judge 203 should-fix 1, and `git rev-parse --is-shallow-repository` returned true in this session.
- **What:** `Git.unshallow()` plus `fno/daily/history.py` `WholeHistory`, run by `DayRunner` before the first step.
- **Choice I made (reasoning only):** a failed fetch is one alert and the day goes on, not a stop. E8's step already
  fails closed in a shallow checkout, and a stop would also lose the quotes and exits. This differs from E8's
  "fail the run loudly"; it is loud (one alert), but it does not stop the run.
- **Tests:** a real shallow clone gets its whole history; a whole checkout is left alone; a failed fetch gives one
  alert; the runner fetches before the day.

### Two changes agreed with the orchestrator, judge D and E4c's owner (16 Oct)

1. **The quote parts start before the Drive download** (judge D's design note; the orchestrator's point 2).
   - `DayRunner` starts the parts before `DailyRun.run`, whose first act is E2c's download, unless the log already
     records `quotes`.
   - After a stop, the runner waits for the parts at least until `desk.timetable.fills_by` (the old 20-minute limit
     counted from a 14:35 stop would have cut them off), then commits each part's own files.
   - Chosen over "skip only the steps that need Drive" (reasoning only): it stays inside O1 and leaves E2c's judged
     stop rule unchanged.
   - Tests: `test_a_drive_outage_at_the_download_never_loses_the_day_s_nse_record`, and the closed-day test
     (recorders record nothing, nothing is committed). Removing the early start fails both.
2. **E4c's double print removed** (`fno/desk/daily_steps.py`), with the agreement of E4c's owner (session
   0134MoC6f7aAJVcHRBiyATo6).
   - The `send` call and its `refused_by_check` gate are unchanged; only the `print` went, because O1's
     `ReportedAlerts` prints the unsent line.
   - `tests/timetable/test_entry_check_alert.py` now wires `ReportedAlerts`, as production does, and pins exactly one
     "alert NOT sent ... trade" line. A planted second print fails it. The reaches-exits check is kept.
   - E4c's two story lines in `docs/stories/E-paper-desk.md` now name `ReportedAlerts`.

### Judge 178 addendum 10 note, made a must by the orchestrator: a hung history fetch

- Both fixes are in. The quote parts now start first, before the history fetch and the Drive download. `Git.unshallow`
  runs its fetch with a hard 120-second limit (`UNSHALLOW_TIMEOUT_SECONDS`; it measured 6.7 s on a fresh clone). A
  time-out is a `GitError`, so it gives one alert and the day goes on, like a failed fetch.
- Tests: `test_a_hung_fetch_is_stopped_at_its_limit_and_is_one_alert`, and the runner order "parts, history, day".

### E6's safety pauses in the daily run (judge 214's gap, orchestrator 16 Oct; a separate commit)

- **The gap:** nothing ran `ScorecardRun` with its pauses. **Strong evidence:** judge E's grep, which I confirmed: no
  caller of `fno desk scorecard` in any workflow or in O1 before this commit.
- **What:** the step `reviews` (`REVIEWS_STEP`, after `exits` in `DAILY_RUN_STEPS`), `fno/daily/reviews.py`.
  - `ReviewsStep` runs a list of `Review`s. Today that is only `ScorecardReview` (E6's real run with
    `pause=True`); LR3 adds the second.
  - Marks come from the day's committed execution snapshot, and the step commits `playbook/`.
  - E6's `build_scorecard_run` takes `alerts=None`, so the run passes its `ReportedAlerts`. O1's graph-walk test
    covers that.
- **Fail-closed:** `DailyRun._unscored`. When the last session's exits ran but `reviews` failed, was refused or never
  ran, every book opens nothing new today; exits run.
- **My choice (reasoning only):** with no valid snapshot the step is refused, not ok, because open positions cannot be
  marked. That blocks the next session's entries until a run marks them. Closed losses still pause.
- **Tests:**
  - `tests/scorecard/test_daily_reviews_step.py`: a catastrophic loss pauses the version the same day through the real
    run; no snapshot gives refused, and the closed loss still pauses;
  - `tests/daily/test_day_run.py`: `_unscored` over 5 cases, and an end-to-end test where day 1's reviews fail and
    day 2's Book 1 opens nothing, with its exits run.
- **Faults planted:** removing `_unscored` from the fills fails the end-to-end test; `pause=False` fails both step
  tests.
- **Judge 178 addendum 13, should-fix 10, accepted and fixed:** an invalid snapshot with no open position would have
  blocked the next session for nothing. It happens in normal running: a capture that fails twice is an O2 family,
  and all 3 books hold no open trades today. Now `Review.review` returns `ReviewResult(lines, open_positions)`;
  E6's count is `sum(len(card.open_marks))` from its own scorecards, so the accounts are not read a second time. The
  step is refused only when the snapshot is invalid and a position is open. Tests cover both ways. Putting the old
  rule back fails the nothing-open test.

### Criterion 8: the CLAUDE.md "Daily desk routine" section (16 Oct, after A4c's live check)

- **Trigger:** the orchestrator, 16 Oct: A4b's live check holds on main 2ec7c6e6 (corrected by the orchestrator: A4c is
  not merged yet; its code is with judge D, so O1's merge waits for A4c's merge). The Groww capture was complete
  (188 contracts, 0 failures, done 14:57:53 IST), the Drive SHA-256 entries and NSE's canonical are present, and no
  Groww quote file is in the repository. Main is merged into the branch; the one conflict was `fno/constants.py`.
  Main's `ENV_GITHUB_OUTPUT` and `PROTOCOL_*` stay there (344 lines). The branch already had the rest in
  `constants_operations.py`.
- **What:** CLAUDE.md's "3 pm quote recorder" section is replaced by "Daily desk routine". It holds the stored prompt
  (one sentence pointing at the section), the setup line (O7's text unchanged), `python -m fno daily run` and its three
  end lines, and the "alert NOT sent" and conversation-log rule. Under it is a sub-section with A4c's steps 2, 3, 3b
  and 4, copied word for word from `story/a4c-all-indices` by script, not retyped. A lead line says the routine never
  runs those commands itself: the run does, and the `git add` lines are the hand fix for "NOT committed".
- **Strong evidence:**
  - A4c's own path test (`tests/quotes/test_routine_commit_paths.py`, from its branch) passes against this CLAUDE.md;
    it was run from a temporary copy, which was not committed;
  - the new `tests/daily/test_routine_section.py` checks that the section names the setup, the command and the stored
    prompt, that no "3 pm quote recorder" section is left, and that `daily run` appears nowhere else in CLAUDE.md;
  - O7's `tests/test_routine_setup.py` now splits on the new heading. That is a one-word change in another story's
    test, made because the section it reads was renamed; its check is unchanged;
  - README's command and routine lines now name `fno daily run`.
- **Merge order (reasoning only):** A4c merges first. A4c's CLAUDE.md change then conflicts with this section, and the
  resolution is this section, which already carries A4c's text. If O1 merges first, A4c's merge takes this section
  the same way.
- **Risk at the switch (reasoning only, for the owner):** after the merge the routine's old stored prompt points at
  a section that no longer exists. The owner should paste the new prompt before the next trading day's 14:33. Until
  then a session following the old prompt finds the "Daily desk routine" section, whose heading names the 3 pm quote
  parts; I cannot prove it will pick that section.

### Criterion 9: one real day (open; cannot close before the merge)

- The routine runs on `main`. `fno daily run` does not exist on `main` until O1 merges, and the owner pastes the
  prompt (O1 never creates or edits a scheduled task). So the real day can only come after the merge. **Proposal:**
  judge D's final addendum passes criteria 1-8 and 10, and criterion 9 is a post-merge check. Its evidence is the
  first trading day's `journal/runs/<date>.json`, the commit list and the card in #fno-desk, added here and checked by
  judge D. S1 counts no day before it.

### Fix: the 3 pm parts' earliest start (16 Oct, `story/o1-part-start`)

- **Found by** O2's end-to-end day (story/o2-failure-handling): a fixture day started at 14:33, the routine's time,
  and NIFTY's part printed "too early: - (0 contracts, complete=False)".
- **Root cause (strong evidence):**
  - A4's recorder refuses a start more than 20 minutes before 14:55 (`fno/quotes/recorder.py` 40, 137-140);
  - O1 started NIFTY's and NSE's parts first thing in the run (judge 178);
  - so a run starting before about 14:35 records neither. That is the routine's own time today if the setup is quick,
    and every day after G10's 14:05.
  - Today's live capture worked only because the old prompt ran `quotes record` after setup.
- **Fix:**
  - `QuotePart.not_before = EARLIEST_START`, which is `WINDOW_START - MAX_EARLY_WAIT_SECONDS + 3 min` = 14:38, taken
    from A4's own constants and not typed;
  - `QuoteParts.start_due()` never runs git and is called from every wait: `service()`, so the desk's
    `ServicingWaiter` and the stopped run's `finish`, and the commands' poll loop, through `waiting` in
    `fno/daily/wiring.py`;
  - the commits stay between the steps, in the run's one thread.
- **Tests:** `tests/daily/test_part_start.py`.
  - A4's real recorder at 14:33 says "too early", and from 14:38 it waits for the window.
  - No part starts before its time; it starts once from `start_due` and makes no commit.
  - Every command of the built run starts due parts while it waits.
  - `test_day_run`'s start time is now 14:38.
- **Faults planted:**
  - no `start_due` in `waiting`: the wiring test fails;
  - no `not_before`: 2 tests fail.

### Criterion 9: the real days (19 and 21 Oct 2026)

Strong evidence: `journal/runs/2026-10-19.json` and `journal/runs/2026-10-21.json` on main, and the commit list on
main.

- **19 Oct:**
  - Every step of `DAILY_RUN_STEPS` was recorded once, in order: `quotes` at 14:37:02 IST through `candles`
    (finished 15:33:20).
  - margin_check, weather, forecasts_v4 and card are `not_live` (`daily.live_from` null), as configured.
  - pack built at 14:58:15. Book 1 decided 2026-10-19-r1, committed 14:58:45.
  - decisions took that run at 15:12. snapshot `nifty_20261019_151500` is valid.
  - fills `{}`: nothing approved to paper. exits reviewed. trade_marks marked `book1_rules` and the shadow
    `b0-monthly-sc-v1`. reviews "0 scorecards". quotes_done "every part ok".
  - The run ended at the catch-up's 15:33 wait.
- **Commits, in order (IST; git prints UTC, add 05:30):**
  - the steps quotes, margin_check, weather and forecasts_v4 at 14:37;
  - **3 pm quotes nifty** adc2c10a at 14:57:57, **first**;
  - **nse** ae7ffeb4 at 14:58:01;
  - versions, pack, the Book 1 decision bd11a8de and book1 at about 14:58;
  - **indices** f8e09ef9 at 15:05:34, after NIFTY's;
  - decisions at 15:12:02, snapshot at 15:18:10, then fills, exits, trade_marks, reviews, quotes_done and card;
  - candles 65e2303f at 15:33:21.
- **20 Oct:** the run recorded only `skipped`: "not a session day" (the calendar's closed day). That is O1's closed-day
  rule, live.
- **21 Oct:** the same shape. NIFTY 80599014 at 14:57:52, then NSE 0b37051c, then the indices 55067976 at 15:05:43.
  Every step was recorded.
- **Not met, said plainly:** the criterion says "the card in #fno-desk". T1's card is not live, so no card was posted,
  and that part of criterion 9 waits for `daily.live_from.card`. The criterion's other three parts are met: every step
  recorded, every record committed, the log and the commit list here.
- **Two related findings:**
  - the rerun crash (story/o1-part-start 6776f7d1, with judge D) was not hit, because no rerun happened;
  - `quotes`' reason says "started nifty, nse" although, since 7b08108c, they start at 14:38. The part's sidecar
    (attempt `nifty_..._145500`) shows the recording waited for its window as designed. The wording is a cosmetic gap,
    and I will make it "nifty, nse from 14:38" in the next O1 change.
