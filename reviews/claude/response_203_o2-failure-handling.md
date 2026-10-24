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

## Code round 1: the hard limit on every git call (9fe595d4)

- **What:**
  - `fno/desk/git_limit.py` (new). `LimitedRun` is a `subprocess.run` for git: each call gets its own process group
    (`start_new_session`). At the limit it kills the group (`os.killpg`, SIGKILL) and reaps it, then removes the
    call's own new locks and raises `TimeoutExpired`, with `removed` set to their names.
  - `GitLocks.present()` lists `.git/**/*.lock`, skipping `objects/` and `lfs/`. `remove_new(before)` removes only
    the locks absent before the call, and nothing while any process named `git…` is alive in `/proc` (judge note 1).
    Without `/proc` it removes nothing.
  - `fno/desk/git_sync.py`: every call goes through `Git._run` with `limit_seconds=GIT_CALL_LIMIT_SECONDS` (120 s), so
    a timeout is a `GitCallStopped` (a `GitError`, hence `CommitFailed`).
    - A git "'…lock': File exists" error gets the hand fix ("no git running? remove <lock> by hand, then rerun").
    - `push()` turns a stop into `PushNotConfirmed` (a `PushRejected`), so `CommitFailed.unpushed` is True and E3's
      rerun recovery handles it.
    - `unshallow` now uses the same limit; its own timeout code is gone.
    - `Git.show()` is new. `content_sha256` and D3's `fno/books/decided_runs.py` use it instead of calling `git.run`
      directly; that direct call was the one path that would have bypassed the limit, and a test found it.
  - `fno/daily/steps.py`: `CommandStep` takes `locks`. On O1's 600 s stop it removes the command's own new locks
    (Book 1's `desk book1` commits by itself), and the reason names them. `fno/daily/wiring.py` passes
    `GitLocks(root)`.
- **Tests:**
  - `tests/daily/test_git_limit.py`, real git with hanging hooks and a 1 s limit:
    - a commit hung in `pre-commit` is stopped within the limit, the hook's process is gone (not running or a zombie),
      no lock is left, and the next commit works;
    - a lock that was already there stays, and the error gives the hand fix;
    - nothing is removed while a git process runs, or when `/proc` is missing;
    - a push hung in `pre-push` is "push not confirmed" and `unpushed`;
    - the default `Git` has the limit.
  - `tests/daily/test_steps.py`: a command stopped mid-commit leaves no new lock, and an older lock stays.
- **Faults planted:**
  - no `unlink` in `remove_new`: the commit test fails;
  - no lock removal in `CommandStep`: its test fails.
- **Not yet proven:** the 120 s value against a real slow GitHub push (reasoning only). The hook-killing relies on
  hooks staying in git's process group, which is git's default; a hook that starts its own session (setsid) would
  survive the stop.
- **Gates:** 7638 passed; ruff, format, check_imports and check_records are clean.

## Revision 6 (judge 204 addendum 4: the shadow replaces `book_test`)

- **What I checked first (strong evidence, read in the code):**
  - A shadow is decided and recorded inside Book 1's run, but **nothing fills, exits or refuses a shadow's orders**.
    `ReplayedOrders.orders` takes `evaluation.chosen`, which keeps only `Decision.CHOSEN`; shadow outcomes are
    `SHADOW_TRADE` (`fno/books/book1_orders.py` 47, `fno/playbook/outcomes.py` 71-72).
  - `fill` and `review_exits` loop over `books` only (`fno/desk/daily_steps.py` 152, 200).
  - Earlier reviews say the same: response_211 line 14, "shadow orders and fills are E8 part 1b's".
  - The only per-account step today is `trade_marks` (`fno/desk/trade_marking.py`, an `except` per account).
- **Consequences, written into the row:**
  - **(a)** isolation at marking can be tested now;
  - **(b)** a Book 1 failure must leave the shadow unchanged;
  - **(c)** a shadow failure inside D2 aborts Book 1's whole decision today. `evaluate.py` 52-59 has no guard. That is
    a real isolation gap. I am reporting it to D2's owner through the orchestrator, and the case is `xfail`, naming the
    gap, until the fix;
  - a refusal of only the shadow's orders cannot be produced, because there are none (judge's point 1, said, not
    dropped).
- **Drive failures:** `AccountWriteRefused` is never reached through the real wiring. A Drive failure is
  `PrivateFilesUnavailable` (a `CommitFailed`) and stops the whole run (`fno/desk/private_files.py` 31 and 100-107,
  E2c's rule), so "account write refused for one account" is not a per-account case today. Row Drive (b) already
  tests the whole-run stop.
- **Fixture, not code:** a `paper` fixture strategy with committed evidence (as `tests/playbook/test_loader.py`
  `approved_repository` builds it), a registered research shadow, a fixture market that fires, and NSE's F&O file for
  C4's listing check. All of it lives in the fresh checkout, and a test proves the source tree's playbook, registry and
  version files are unchanged.
- **Correction of my own earlier claim:** I first told the orchestrator that "Book 1 has no registered version, so
  nothing trades". The version registry only affects scoring. The real reason nothing trades is that the registry
  holds no `paper` strategy. The row and the Known limits say so.
- **Criterion 8:** one fixture day takes 6-7 s through the real wiring. About 35 days cannot finish in a minute, so
  the limit becomes two minutes on four cores, measured, not guessed.

## Code round 2: the end-to-end harness (47b6212d, 40635d55, efd78e12, b96ff5b0)

- **What:** `tests/e2e/` runs `fno daily run` through `fno/daily/wiring.py` `build_day_runner`, in a fresh checkout
  with its own bare origin.
  - The checkout holds a copy of `fno/`, `playbook/`, `journal/versions.csv`, `config.yaml` and `.gitignore`.
  - The paper accounts live in the fake Drive.
  - Only the names in `OUTSIDE_SEAMS` (`tests/e2e/harness.py`) are replaced, and a test checks the list:
    - the clock (`fno.models.datetime`; git dates every commit by it through `GIT_COMMITTER_DATE`);
    - Slack;
    - the owner's Drive (two bindings);
    - the raw NSE stores;
    - NSE's archive (three bindings);
    - Groww's 15:15 capture (A4's real recorder over `FixtureProvider`);
    - the child commands (`tests/e2e/children.py`);
    - the quote store's default folder (the real store, with the checkout's folder).
  - The child commands: NIFTY's part runs A4's real `record_today` on its own clock, in its own staging folder, and
    lands in the checkout when the run sees it end. Book 1's decision runs the real `build_book1(...).decide`.
- **Production changes, each tested:**
  - `build_day_runner(cfg, root, sleep)`: the run's waits take the injected sleep;
  - `build_book1_orders(cfg, root)`: the run used the package's ROOT for Book 1's code tree. A decision committed
    in the run's checkout would then fail the replay ("the running fno/ and config.yaml differ"). It is harmless in
    production, where root is ROOT, but it is a real case of ignoring the injected root;
  - the execution capture's quote folder is now `root / QUOTES_FOLDER.relative_to(ROOT)` (`fno/desk/daily_wiring.py`).
  - Tests: the normal day itself, which ends "day done" with no alert and fails without either fix, plus the
    adjusted fakes in `tests/daily/test_steps.py`.
- **Process note (said plainly):** 47b6212d was pushed to the story branch with two failing tests and one lint error,
  because my chained command did not stop on a failure. 40635d55 fixed it. Since then every push goes through a gate
  script that exits non-zero.

## Code round 3: the outage families and G1 (aab33abd, af9e9dd3)

- **Tests:**
  - `tests/e2e/test_outages.py`: Groww down all day; NSE failing; Drive down at the download; Drive down for raw
    files. Each runs with Slack up and Slack down. The twin test compares, as one multiset, the alerts the owner gets
    either way. "No step whose data did not land records ok" holds for the quote parts.
  - `tests/e2e/test_never_starts.py`: a skipped session is O8's `missed`, and the next session blocks every book
    once (`NO_LOG`) and still reviews its exits. The same holds after a Drive outage at the download.
- **G1, a gap in O1's own code, fixed:** `quotes_done` is `status_alerts=False`, so a part that failed without
  alerting for itself was never alerted. That is a Groww outage: `quotes record` ends incomplete with no alert. Now
  `QuoteParts._alert` sends one line for a failed part whose lines carry no alert outcome, and for a part stopped or
  never started. A part that did alert for itself gets no second line.
  - Test: `test_a_failed_quote_part_is_alerted_once_by_itself_or_by_o1...` in `tests/daily/test_day_run.py`. It
    replaces the old "gets no O1 alert" test, whose rule was wrong.
  - Fault planted: no `_alert` call, and 5 tests fail.
- **G2, reported, not mine:** a child prints only "alert NOT sent: <reason>", not the alert's text (`fno/quotes/cli.py`
  `record_today`). The orchestrator assigned it to the A4 builder (story/a4-unsent-alert-text). Strict xfail:
  `test_drive_down_for_raw_files...[slack-down]`.

### Round 4b: G4's strict xfail becomes the real assertion (after O1's G4 merged, d1983cc6, judge 420)

- `tests/e2e/test_hangs.py::test_a_quote_part_s_push_that_hangs_is_alerted_not_pushed_the_next_push_carries_it_and_the_desk_goes_on`
  replaces the strict xfail.
  - The test asserts the alert "quote part nifty committed, NOT pushed (the next push carries it)" with "push not
    confirmed", and that the part's commit then reaches origin through the desk's next push. It also asserts that the
    exits are reviewed and that no git lock is left behind.
- F1's strict xfails, in `test_kill_rerun.py` and in `test_hangs.py::test_the_rerun_after_a_stopped_push_ends_day_done`,
  stay strict until O1's F1 code merges.

### Round 4a: F1's strict xfails become real assertions (O1's F1 code, judge 421 and add. 1 PASS, merged in)

- **What the run does now (strong evidence, read from the run itself):** after a kill following any step before
  `quotes_done`, the rerun ends `day done` with no alert. Its committed tree and Drive files equal the twin's,
  except for the run log. Every step other than `quotes_done` matches the twin. The parts resume as follows:
  - killed at the desk (snapshot through reviews): each part is taken as "earlier run";
  - killed between versions and the decisions, before the indices ended: NIFTY and NSE are "earlier run" and the
    indices are "restarted";
  - killed before versions (from 14:33): all three are "restarted".
- **`tests/e2e/test_kill_rerun.py`:** one test, `test_a_kill_before_quotes_done_reruns_to_the_twin_s_bytes_and_resumes_each_part`,
  replaces three tests that asserted the old outcomes (`NOT_IN_THIS_RUN`, a lost indices record, and the strict
  xfail). It is parametrized over every step before `quotes_done`, with the expected `how` of each part. The test for
  kills after `quotes_done` is unchanged: the twin's bytes.
- **`tests/e2e/test_hangs.py`:** the desk-hang rerun now ends `day done`, with each part "earlier run". The strict
  xfail `test_the_rerun_after_a_stopped_push_ends_day_done` asserted the same thing, so it was removed into that test
  rather than kept as a duplicate.
- **Merge:** O2's `NOT_IN_THIS_RUN_ALERT` (quote_steps), the whole-step alert, gives way to F1's per-part alert. Every
  part that is not recorded still alerts once, so "never silent" holds.

### Fix: the hung-git test was timing-sensitive under load (judge E, 22 Oct; branch `story/o2-git-limit-test`)

- **The flake (judge E):** `tests/daily/test_git_limit.py::test_a_commit_hung_in_its_hook_is_stopped_with_the_hook_and_leaves_no_lock`
  failed once in a full parallel run (one run took 40 s against about 4 s). It passed alone 3 of 3.
- **Root cause (strong evidence, by experiment):** the test put its 1 s limit on every git call, not only on the hung
  one. `Git.commit_paths` makes four calls (`add`, `diff --cached` twice, `commit`), and the test's final "the next
  commit works" makes four more.
  - The hung call's 1 s also started at `Popen`, before git had even reached its hook.
  - On a loaded machine, any normal call can pass 1 s, or the hook can start after it.
  - Reproduced with a `git` shim that adds 1.2 s to every call. The test failed with `git add -- ran past 1 s and was
    stopped with its hooks`: the limit had stopped a normal call, not the hung commit.
  - The same shim showed the same flaw in `test_a_lock_that_was_there_before...` (its `git add`). CPU burners or a
    concurrent full suite did not reproduce it in 2 × 40 repetitions, which fits a rare stall.
- **Fix:**
  - `LimitedRun(started=...)` (`fno/desk/git_limit.py`): a callback, called once the call runs and before its limit
    counts. The daily run passes nothing, so production behaviour is unchanged.
  - In the tests, `HungCallRun` keeps the short limit for the hung call only and starts it once that call's hook has
    written its pid, which means git holds its lock. Every other call keeps the run's own 120 s limit. The pre-existing
    lock test uses the run's limit.
  - The timing assertion is now measured from the hook's start. It proves the call was stopped by the limit and not
    by the hook's own end (`< HOOK_SLEEP / 20`, 30 s against the hook's 600 s).
- **A second failure mode, found by the A4 builder (22 Oct, one failure in 5 full runs on main):**
  `assert not _alive(pid)` saw the hook still alive right after the call.
  - Cause (strong evidence, from the code): `killpg` only sends SIGKILL, and each member ends when the kernel reaches
    it. `communicate()` waits for git, the group's leader, and its pipes, but not for the hook, git's grandchild.
    So "stopped with its hooks" could be said while the hook was still dying.
  - Fix, the A4 builder's option (a), refined: `LimitedRun._until_gone` waits until no live member of the group is
    left (`running_in_group`, read from `/proc`), at most `GROUP_GONE_SECONDS` (5 s).
  - A zombie counts as gone: it holds nothing, and in a container its new parent may never reap it. Polling
    `killpg(pgid, 0)`, which also counts zombies, could then wait the full 5 s on every stop.
  - Tests: on a fake `/proc`, a live member counts, a zombie does not, another group does not, and no `/proc` means
    no wait. The wait is bounded when the group never ends.
  - Limit (stated plainly): a plant that removes `_until_gone` is not caught deterministically. The race it closes
    shows only under load, so the unit tests guard `running_in_group` and the bound instead.
- **Proof:**
  - All 7 tests pass with every git call slowed by 1.2 s, longer than the limit itself.
  - Plants: removing the lock clean-up fails 1 test; killing only git instead of its group hangs the test (the hook
    holds the pipes).
  - Ten full parallel suite runs (`pytest -q -n auto`) on a708fbc0, back to back: 9479 passed, 16 xfailed, 0 failed
    in every run (5:14 to 5:56 each).
- **The same flaw in the e2e hang tests (judge D's go-ahead in 412 add. 7):** `tests/e2e/test_hangs.py` set a 2 s
  limit on every git call of a whole fixture day.
  - Reproduced: with every git call slowed by 2.5 s, the test failed with `git ls-files -z ran past 2 s`, a normal
    call stopped instead of the hung push.
  - Fix, test-only (002d64c5): `HungCallRun` moves to `tests/daily/hung_calls.py`, with `when=` and `locks=`. The e2e
    day gives the short limit only to a push made while `.git/hang-push` exists, counted once that push's hook has
    written its pid. Every other call keeps the run's own limit. The hook now writes the pid.
  - Proof: with every git call slowed by 2.5 s, all 3 e2e hang tests pass (28:49 of slowed git).
