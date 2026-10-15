# Judge 178: O1 daily run, code round 1 (story/o1-daily-run at 75d2aa14)

**Verdict: PASS for round 1's scope** (the parts that do not wait for E2c). There is no blocking finding and no
should-fix. Five notes follow. Notes 1 and 2 must be done before the final code PASS or before the merge. Criteria 8
and 9 are not built yet (the reasons are below), so this is not the story's final code verdict.

Story text: `docs/stories/O1-daily-run.md` at 75d2aa14 (text PASS, judge 169 addendum 1). Claims:
`reviews/claude/response_165_o1-daily-run.md`, sections "Code round 1" and "O8 swap".

## Gates

- **Trial merge with origin/main as it was when checked:** clean. `python -m pytest -q` gives 6039 passed (claimed
  6038; main had moved on). `ruff check`, `ruff format --check` and `tools/check_imports.py` are all clean.
- **Trial merge with origin/main at fb4ced9f** (after the LR1 merge a024225a): CLAUDE.md conflicts in the
  composition-root list, and `fno/constants.py` becomes **351 lines**, over the 350 limit, so `tests/test_code_size.py`
  would fail. See note 2.

## Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Order and days | MET | `test_a_session_runs_every_step_once_in_the_tuple_s_order` (log keys == `DAILY_RUN_STEPS`); the closed-day test; muhurat-only and special sessions keep E3's `RECORDED_SESSION_KINDS` |
| 2 | A failure never stops the next step | PARTLY | Raise and refusal are tested for `weather`, `forecasts_v4` and `book1`. **Not tested:** `card`, `quotes` (a raise in the start step), or a planted failure of each quote part. My probe on the branch's fakes: a raising `card` gives `failed`, one alert and "day done with problems: card"; a NIFTY part that exits 1 gives no O1 alert, NSE and the indices still commit, and the result is "not ok: nifty". So the behaviour is right and only the tests are missing (note 1). The stop test passes as written: the card never runs, E3's alert stands alone and the parts still commit |
| 3 | Restart | MET | `test_a_rerun_skips_every_recorded_step_and_restarts_no_part` |
| 4 | The quote parts are A4c's | PARTLY | Covered: start times (NIFTY and NSE at the run's start), indices after NIFTY's commit, NIFTY committing first, the desk's times unmoved by a 15:13 part, and a hung part. **Not tested:** the story's "a planted NIFTY failure..." case (probe above; note 1) |
| 4a | One git at a time; pathspec commit | MET | Real git: `test_each_part_commits_only_its_own_files_with_another_file_staged`. My mutation removing `-- <paths>` from `commit_paths` fails it |
| 5 | The card is T1's, last, never after the stop | MET | Order test and stop test |
| 6 | Not live | MET | `LiveFrom` tests; `config.yaml` `daily.live_from` all null |
| 7 | O8's contract | MET | O8 imports `DAILY_RUN_STEPS`; its private tuple and source-parsing test are gone; failed or refused are problems, `not_live` is neither missed nor a problem (new tests) |
| 8 | One prompt (CLAUDE.md section) | NOT BUILT (stated) | Waits for A4c's merge so it can carry A4c's lines word for word |
| 9 | Real day | NOT BUILT (stated) | Waits for the owner pasting the prompt |
| 10 | Engineering | MET at 75d2aa14 | `DayStep` interface; wired in `fno/daily/wiring.py` (listed in CLAUDE.md); largest new file 135 lines; no secret; never orders. Merge note 2 |

## Claims checked against reality

- **"The parts never run git."** True. `fno/quotes`, the weather and v4 capture modules have no git calls. The card only
  reads git (`GitHeadRecords`) and runs in the foreground after `quotes_done`. `desk book1` does run git (E5b's own
  commit), but it runs in the foreground while the run's only thread is blocked in `wait()`, so it never interleaves
  with a part's commit.
- **Pathspec commits keep the record scan.** Checked in a scratch repository with the real `.githooks`: a part file
  holding a planted e-mail address, committed through `Git.commit_paths` by pathspec, is refused by the scan
  ("e-mail address", values not shown). Nothing was committed.
- **Planted faults.** I re-planted two of the builder's four: no `--` pathspec, and indices that do not wait for NIFTY.
  Each made `tests/daily` fail (1 and 2 failures); both were reverted.
- **`fno desk run` removed.** Nothing calls it (no workflow, CLAUDE.md or routine line). Its CLI test is replaced by
  the runner's stop test and the `daily` CLI test.

## Text amendment: the `book1` step (accepted)

Reason: on main nothing calls `fno desk book1`. A `grep` of `.github/`, CLAUDE.md and the docs finds no caller, and
E5's own docstring said "No routine starts them yet". E3's `decisions` step only collects committed D3 records, so
without this step Book 1 records "no decision (late)" every session.

Placement is right. It runs after `pack`, which it needs, and before the 15:12 deadline. Its pathspecs are empty,
so the run sweeps up nothing of its own. E5b, which owns `fno/books/book1*`, is merged (bd6ff1e2 is on main), so
removing `add_run_command` from `book1_cli.py` collides with no open branch.

The stated duplicate alert on a failed Book 1 commit (E5b's alert plus "step book1 failed") is acceptable.

## Notes

1. **(Before the final code PASS) Close the criterion 2 and 4 test gaps.** Add a raise for `card` and `quotes`, a
   planted failure (non-zero exit) for each quote part, and the NIFTY-failure case. The behaviour is already right (my
   probe), so these are tests only.
2. **(At the merge) The merged tree overflows `fno/constants.py`.** With main at fb4ced9f the file reaches 351 lines,
   and CLAUDE.md's composition-root list conflicts with LR1's addition. When merging, split a cohesive block out of
   `fno/constants.py` (never squeeze lines) and keep both composition-root entries. Then re-run the full suite on the
   merged tree.
3. **(Merge order) O1 merges only after A4c.** `quotes record-indices` does not exist on main yet. If O1 lands first,
   the indices part would fail every day with an argparse error, recorded quietly under `quotes_done` (no alert by
   design). This is already implied by the CLAUDE.md section waiting for A4c; stated here so the merge check holds it.
4. **(Optional) A rerun after a died run.** The rerun's `quotes_done` records `NOT_IN_THIS_RUN`, and any part files
   the dead run wrote stay uncommitted until fixed by hand. The rerun could commit what it finds under each part's
   pathspecs. A session dying mid-day is a stated known limit, so this is not a should-fix.
5. **(Register) Ownership of the prompt.** `docs/WORK_REGISTER.md` still lists the Handover / routines row as owning
   "CLAUDE.md 3 pm section, routine prompts", and O1's row claims the same files. The orchestrator's ruling gives the
   prompt to O1 (story text, "Ownership of the prompt"). The orchestrator should update the Handover row so the
   register shows one owner. The E5b row also still reads "after E2c" although E5b is merged.

## Addendum 1: delta to 22e4dd7f (margin_check step, constants split)

**Verdict: PASS for round 1's scope.** This delta adds no blocking or should-fix finding. Note 2 is closed. Note 1
stays open: the criterion 2 and 4 tests have not arrived yet. Note 6 is new and optional.

- **Gates on a trial merge with origin/main (4e72c4e4 line, 15 Oct evening):** 6142 passed. `ruff check`,
  `ruff format --check` and `check_imports` are clean, and `tests/test_code_size.py` passes. `fno/constants.py` is now
  341 lines and `fno/constants_operations.py` 37.
- **The split (closes note 2).** The daily-operations block moved out whole. All 15 names in `__all__`
  (`RUN_LOG_DECISIONS_STEP`, the two step tuples, O1's four statuses and O8's health names) read the same through
  `fno.constants` as through the new module (checked in Python). The health values equal main's lines 343-346, and
  `RUN_LOG_DECISIONS_STEP` is still "decisions". It is one `import *` driven by an explicit `__all__`, so no caller
  changes. This is a split, not a squeeze. The CLAUDE.md conflict is resolved: both the LR1 and O1 composition roots
  are listed.
- **`margin_check` (text amendment, accepted).** It records A14c's agreed line (decision da0f769d; the A14c builder,
  15 Oct) as O1's first step. It runs the unchanged command, commits only `stress_broker_check.csv`, and stays
  `not_live` (`daily.live_from.margin_check: null`) while the command does not exist, so nothing calls Groww today.
  Tests: the order, failure and rerun tests now include it. The new wiring test shows the composition root gives every
  name in `DAILY_RUN_STEPS` a step.
- **T2's note (judge 180): the card comes after `decisions` and after 15:15.** MET by the order. `card` follows
  `quotes_done`, which follows `exits`. `exits` waits until `desk.timetable.execution_snapshot` (15:15), so the card
  can never start before 15:15 or before `decisions` (15:12).

6. **(Optional, reasoning only) Put `margin_check` after `quotes`, not before.** Each `CommandStep` waits for its
   child with no time limit. As the first step, a Groww call in A14c's command that hangs would hold back the start of
   the quote parts, the day's main data. The parts are child processes that wait for 14:55 themselves, so starting
   them first costs nothing and still avoids overlapping the 14:55 capture on the Groww key. There is no evidence of a
   Groww hang, so this is not a should-fix. Otherwise, when A14c lands, confirm its Groww request has a timeout.

## Addendum 2: O1 at f22ffc42 (note 1 tests; E2c merged in)

**Verdict: PASS for the code built so far.** No blocking or should-fix findings, and notes 1, 2 and 4 are closed.
Criteria 2 and 4 are now MET. Still to come before the story's final code verdict: criterion 8 (the CLAUDE.md section,
after A4c) and criterion 9 (the real day).

- **Note 1 closed.** New tests:
  - `test_quotes_or_card_raising_is_recorded_failed_with_one_alert` (quotes, card);
  - `test_a_quote_part_that_exits_non_zero_gets_no_o1_alert_and_the_others_still_commit` (each of the 3 parts);
  - `test_a_failed_nifty_still_starts_the_indices_after_it_and_lets_nse_commit`.

  Each asserts what my probe found: one O1 alert for a step that raises, none for a part (A4c's own alerts stand),
  the others still commit, and the indices start when NIFTY ends, whatever NIFTY's result.
- **Note 4: declined, and I accept the reason.** A killed recorder can leave a half-written sidecar or canonical, and
  only the recorder can tell whether an attempt is complete. Committing blind could put a broken record on `main`. The
  limit is now a Known-limits line.
- **E2c merge.** The resolution keeps both additions: E2c's `files` (private records downloaded before any step) with
  `_unreviewed` passed to `fills`, and O1's `day_steps`. `build_daily_run` passes both. The real-git pathspec test now
  stages a tracked file of another writer, because E2c ignores the account files in git. That is right: the test still
  proves a staged file is never swept in.
- **Gates on a trial merge with origin/main f78c7759:**
  - 6175 passed, 3 failed;
  - plain main at f78c7759, run at the same time: 6118 passed and **the same 3 failed** (`test_paper_account` 15 Oct
    top-up, `test_committed_closes_reproduce_the_disclosed_v6_counts`, `test_home_blocks` live wiring);
  - none of the 3 is in O1's files, so the builder's claim holds. Merge rule: they must be green on main (their owners'
    fix) before O1 merges, since the merge needs the full suite green on the merged tree;
  - `ruff check`, `ruff format --check` and `check_imports` are clean.
- Note 3 (merge after A4c) stands, and so does optional note 6 (start `quotes` before `margin_check`). The builder
  did not mention note 6.

## Addendum 3: O1 at 43943a52 (note 6 built: quotes first, 10-minute command limit)

**Verdict: PASS for the code built so far.** No blocking or should-fix findings. Note 6 is closed. Criteria 8 and 9
and the merge after A4c are still to come.

- **Order.** `DAILY_RUN_STEPS` now starts with `quotes`, then `margin_check`, so the quote parts (child processes that
  wait for 14:55 themselves) always start before any command that might call Groww. My mutation swapping the two
  makes `tests/daily` fail. The story table and the "No command holds the day" line match the code.
- **Limit.** Every O1 `CommandStep` (margin_check, weather, forecasts_v4, book1, card) is stopped after
  `COMMAND_LIMIT_SECONDS` = 600 and recorded `failed`, with nothing committed. The new test proves the stop, the
  10-minute bound and the empty paths. My mutation removing the limit makes it fail.
- **Gates on a trial merge with origin/main:**
  - 6176 passed, 3 failed: the same 3 that are red on plain main (judge 178 addendum 2), none in O1's files;
  - `ruff check`, `ruff format --check` and `check_imports` are clean.

Notes (one line each, reasoning only, not should-fix):

7. A 10-minute limit does not protect the 15:12 deadline for `book1`, which starts after the pack (up to about
   15:10). A hung `book1` could push `decisions` to about 15:20. E3's late rule then applies and the exits still run,
   so no trade or stop is decided wrongly. The claim "never holding the deadline" is too strong for `book1`.
8. `ChildProcess.stop()` kills only the Python child. A `git push` that `book1` started could outlive it and touch
   the checkout while the run goes on. No evidence that this happens, and a 10-minute hang of `book1` has not been
   seen either.

## Addendum 4: O1 at 71b00878 (notes 7 and 8)

**Verdict: PASS for the code built so far.** No blocking or should-fix findings. Notes 7 and 8 are closed.

- **Note 7.** The `CommandStep` docstring and the story's "No command holds the day" line now say plainly that the
  10-minute limit does not protect 15:12 for `book1` (which can start at about 15:10), and that E3's late rule
  decides that case. The claim now matches the behaviour.
- **Note 8.** Children start with `start_new_session=True`, and `stop()` kills the whole process group (`killpg`,
  SIGKILL; a child that already ended is tolerated). This also covers a quote part stopped at `FINISH_LIMIT`. The new
  test, `test_stopping_a_command_kills_what_it_started_too`, uses a real grandchild and checks it is dead (zombies
  count as dead). My mutation removing `start_new_session` makes it fail.
- **Gates on a trial merge with origin/main dd35b2e5:** the suite is now **fully green, 6180 passed** (main's fixes
  for the 3 earlier red tests are in). `ruff check`, `ruff format --check` and `check_imports` are clean.
- One-line note, reasoning only: in their own session, the children no longer receive a Ctrl-C or SIGTERM sent to
  the routine's process group. If the run itself dies, a running recorder carries on with no one to commit its files.
  That was already the case for a crashed parent, and the stated known limit (a rerun after a dead run) covers it.
  Nothing to change.

Still to come: criterion 8 (the CLAUDE.md section, after A4c), criterion 9 (the real day), and the merge after A4c.
