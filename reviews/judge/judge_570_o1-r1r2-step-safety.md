# Judge 570: O1's DRY2 fixes R1 and R2, story/o1-r1r2-step-safety

- **Judge:** E (session_01HkXMVPDEqVsmJZtghFrGzM), lane 1 (the money path), round 1 of 2
- **Head judged:** e8dc9498, which already contains main
- **Claims:** docs/stories/O1-daily-run.md, "Fix after DRY2: the indices' own early limit and one failed step
  never ends the day"
- **Verdict: PASS. Merge go,** before Mon 26 Oct 14:05 IST.

## Gates
- pytest -n auto: 15115 passed, 0 failed.
- ruff check, ruff format --check, check_imports, check_records: clean.

## R1: the indices wait for their own early limit (code read, plants)
- The indices part's `not_before` is now `INDEX_EARLIEST_START`. It is computed from A4c's own window by
  the same rule as NIFTY's (14:44 today).
- `start_due` starts a part only when three things hold: it is unstarted, the part it waits for has ended,
  and its own time has come. `service` ends by calling `start_due`, so the old path that started a waiting
  part regardless of its time is gone. `next_start` counts a waiting part once its leader has ended, so the
  run's waits wake for it.
- Plants:
  - R1a (no early limit for the indices): caught.
  - R1b (a waiting part ignores its limit): caught.
  - R1c (`next_start` skips waiting parts): caught.

## R2: one failed step never ends the day
- `_run_step` catches any other `Exception` in an in-process step. It logs the step failed as "Type: first
  line", sends the alert, and the run goes on. `CommitFailed` and `GitFailed` are re-raised and still stop
  the run through `_guarded`.
- Only in-process steps change: versions, pack, decisions, snapshot, fills, exits, marks and the in-process
  day steps. The child-process steps, such as `book1`, were already non-fatal through `Alerted`.
- The deliberate refusals stay where they were: `OrdersRefused` and `AccountWriteRefused` are caught per
  book or trade inside `fill`. No step's stop signal is swallowed, because `RunStopped` comes only from
  `_guarded`.
- `fills` is refused when snapshot or decisions failed. Exits and marks still run, so risk-reducing exits
  happen. A failed exits step makes every book unreviewed the next day, so no book opens anything new.
- Plants:
  - R2a (catch narrowed): caught.
  - R2b (`NEEDS` dropped): caught.
  - R2c (the failed-exits rule dropped): caught.
  - R2d (commit and git failures swallowed): caught, 8 failed.
  - R2e (git failures swallowed): caught.
  - R2f (no alert): caught.
- Before R2, a pack or snapshot exception stopped the whole run before its exits. Now the exits run. That
  is the safer direction for open positions.

## Minor (not blocking)
1. **R2b2 survives:** `NEEDS` without "decisions" passes every test.
   - It is close to harmless: a failed decisions result holds only `status` and `reason`, so `fill` finds
     no book's `run_id` and fills nothing.
   - Pin it with one test, so the refusal does not rest on that accident.
2. **A partial fill reads as nothing filled.** `fill` writes each trade to the account as it goes. An error
   after some trades leaves them in the account, which exits then review correctly, while the run log and
   the alert say "step fills FAILED" with no trades listed.
   - Suggest the fills alert adds "trades written before the error stay in the account; check it", so the
     owner is not misled.

## Plants: 10 planted, 9 caught, 1 survived (R2b2, minor)
