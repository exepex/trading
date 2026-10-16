# Response 203: story O2, failure handling end to end (story text, claims for the judge)

Branch `story/o2-failure-handling`. Text: `docs/stories/O2-failure-handling.md`. Lane 1. Code after O1 merges
(owner, 16 Oct; orchestrator).

## Claims

1. Each failure behaviour O2 tests is already built and judged in its own story: C3, C4, E3/E2b, E2c, O1 and O8.
   O2 adds a suite, not new behaviour. **Strong evidence:** the files named in the text's context section.
2. No test today drives the whole day through a real outage. Each part is tested with fakes for the rest.
   **Strong evidence:** `tests/timetable/`, `tests/daily/`.
3. REPLAN's "monitor heartbeat" belongs to LM1, which is not built. O2 builds no second heartbeat (one builder per
   function). The daily routine's own "never started" chain (no log, then O8's "never ran", then the next session's
   entry block) already exists and is proven here. **Strong evidence:** `REPLAN_new_stories.md` LM1, design 4.2 and
   6.5, and `DailyRun._unreviewed` with `NO_LOG`.
4. Design 9's AI rows ("a role fails to report", "judge or AI unavailable") cannot be tested until the AI books trade
   (F5/F6). **Strong evidence:** the work register; no AI order code on `main`. Broken protection is in scope: E4c
   merged at 4d2dc961, and its three reason codes and its alert are tested as E4c's text states them.
5. A kill-after-each-step rerun that gives byte-identical records is the right test of "a partial run and its
   rerun": E3's rule is that a rerun repeats nothing. **Reasoning only** until the suite runs.
6. Today's run alerts do not follow design 6.5's first-line rule. I recommend a separate story for that.
   **Strong evidence:** the alert templates in `fno/daily/steps.py` and `fno/desk/daily_run.py`. The recommendation
   itself is reasoning only.

## Revision 2 (orchestrator, 16 Oct)

- Heartbeat: agreed as written (LM1's).
- E4c merged (4d2dc961), so a broken-protection family is added: E4c's three refusals, `not_opened`, one alert, never
  half-hedged, no quote figure in the record.
- The design 6.5 first-line rule: a separate story after O1 merges. It is a Known-limits line with that pointer.

## Revision 3 (judge 204 FAIL, 399f3dbf): all three should-fixes and the four notes accepted

I checked each one against the code before accepting it.
1. **Accepted.** `PrivateFilesUnavailable` is a `CommitFailed` (`fno/desk/drive_sync.py` line 6), so a Drive failure
   at an account write stops the run at `fills`: no exits that day, and `BEFORE_EXITS` blocks every book next
   session. The row now states that rule; only `AccountWriteRefused` and `OrdersRefused` fail one book closed.
2. **Accepted, option (a).** One test-only second book `book_test` goes through `build_daily_run`'s existing `books`
   parameter, as the single exception to criterion 6. Reason: design 13.5's isolation can then be proven now, not
   only after F5/F6 (reasoning only).
3. **Accepted.** For kills from `quotes` to `exits`, the rerun records `quotes_done` failed (`NOT_IN_THIS_RUN`) and
   leaves the part files uncommitted (O1's decision). That outcome is now named in the row, byte-identity is kept for
   the rest, and a kill between a step's record and its commit is added.

Notes:
- **A, accepted:** a Drive failure at the download loses the day's quote parts, NSE included.
- **B, confirmed and routed:** `fno/desk/daily_steps.py` lines 191-193 print E4c's outcome themselves, so an unsent
  refusal would print twice under `ReportedAlerts`. Sent to the orchestrator for E4c's owner.
- **C, accepted:** `NO_LOG`'s wording also covers a run that never began.
- **D, accepted:** the step count is read from `DAILY_RUN_STEPS`.

## Revision 4 (16 Oct, after O1's merge)

- **Hard limit on every git call (orchestrator, 16 Oct: "take the git-call hard limits inside O2").** Strong
  evidence, `fno/desk/git_sync.py`: `Git.__call__` runs `subprocess.run` with no `timeout`; only `unshallow` has one
  (120 s). So a hung pull, commit or push blocks the run's one thread, the 15:15 exits included, and E3's judged rule
  "a failed commit stops the run with one alert" is never reached. The planned fix, in O2's code: every git call of
  `Git` goes through one hard limit (`GIT_CALL_LIMIT_SECONDS`, 120 s, the fetch's limit), and a timeout is a
  `GitError`, which `GitCommitter` already turns into `CommitFailed`. The choice of 120 s for every call is reasoning
  only: today's pushes take seconds, and a call past two minutes is hung. Test row: "Hung git call", in a desk commit
  and in a quote part's commit.
- **Hung command row:** O1's 600 s limit (`COMMAND_LIMIT_SECONDS`) in the end-to-end suite.
- **Row (a) corrected:** since O1's judge 178 round, the quote parts start before the download (`fno/daily/runner.py`
  `run`), and a stopped run waits for them to commit (`_finish_parts`). So a Drive outage at the download no longer
  loses the day's quotes.
- **Criterion 5:** "Book 2" corrected to `book_test` (judge 204 addendum 1's note).
- **Judge 204 note B closed:** E4c's own print is gone (O1, with its owner's agreement), and the existing test asserts
  exactly one unsent line.
- **Later steps** (F1t, G13, A16b, Book 2's rule default): covered by the tuple-driven kill cases and `Alerted`. O10's
  boundary is being agreed (one alert per failure).

## Revision 5 (judge 204 addendum 2, should-fix 1: accepted)

- **The finding, checked:** a commit stopped at the limit leaves `.git/index.lock` (and `next-index-<pid>.lock`),
  the hook keeps running, and every later git call then fails with "File exists". I accept it. The mechanism is
  sound: git holds `index.lock` for the whole commit, including the pre-commit hook, and a kill of git alone leaves
  both the lock and the hook. I will reproduce the judge's test as the suite's first case.
- **The design now in the row:**
  - each git call gets its own process group (`start_new_session=True`), and on the limit the whole group is
    killed and waited for, the same way as `fno/daily/processes.py`;
  - the lock files that call created are then removed. They are found by comparing `.git/**/*.lock` before and
    after the call, so only locks absent before it are touched. That is safe because the run's git is
    single-threaded and nothing else of the run runs git during a call (the child commands are waited for);
  - a lock that was already present is never removed. The call fails at once, and the alert names the lock and the
    hand fix.
- **A stopped push** is "push not confirmed" and is marked unpushed, so E3's rerun recovery deals with it (the
  judge's note).
- **"The next day's routine":** the routine starts in a fresh container (`fno/desk/daily_run.py` 122), so a lock
  left in one container cannot reach the next day's clone. That is some evidence, read from the code, not tested
  live. The test still checks the next day's first commit in the same checkout, which is the stronger case.
- **Tests:** a real git repository with a hanging pre-commit hook and a short limit. They check that:
  - the hook's process is gone;
  - no lock created by the stopped call is left;
  - the next quote part's commit and the next desk commit succeed;
  - a lock present beforehand is left alone and gives the one named alert.
- **The same hole in O1's command limit (found while fixing this one):** a `CommandStep` stopped at 600 s while its
  command is inside a git commit leaves the same locks. Book 1's `desk book1` commits its own decision. The row "Hung
  command" now uses the same lock rule, and a test kills it mid-commit.
