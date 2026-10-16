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
