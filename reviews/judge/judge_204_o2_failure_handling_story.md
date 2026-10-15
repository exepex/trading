# Judge 204: O2 failure handling, end to end (story text at a06799a6)

**Verdict: FAIL, 3 should-fix.** The suite is the right idea: one end-to-end run with fakes only at the edges, no new
behaviour, and LM1's heartbeat left to LM1. But three of the expected outcomes contradict the code they say they
follow, and criterion 7 ("none hidden by a test that expects the wrong outcome") forbids writing a test to the wrong
outcome. The code was read on origin/main after E2c and E4c, and on O1's branch at f01bf9d7.

## Criteria

| # | Criterion | Result | Why |
|---|---|---|---|
| 1 | Each family's outcome is the owner code's rule | NOT MET | should-fix 1 and 3 |
| 2 | Exits run or are held with an alert | MET as text | `review_exits` runs for every book; with no pack the gate leaves exits `waiting` with its alert |
| 3 | No alert is lost | MET as text | see note B for a gap the suite will find |
| 4 | A rerun repeats nothing | NOT MET | should-fix 3 |
| 5 | Books are isolated | NOT MET | should-fix 2 |
| 6 | Fakes only at the edges | PARTLY | in conflict with 5 (should-fix 2) |
| 7, 8 | Real failure, real fix; engineering | MET as text | |

## Should-fix

1. **Drive outage (b): the row contradicts E2c's rule.**
   - **The text says:** a Drive failure at an account write during fills makes "that write's entries fail closed with
     an alert, while other books and every exit go on".
   - **The code says otherwise:** `DriveAccountSync` (`fno/desk/drive_sync.py` docstring) states that Drive failing
     (`PrivateFilesUnavailable`, a `CommitFailed`) "stops the write: E3's one handler alerts and stops the run". So
     `_guarded` raises `RunStopped` at `fills`: the stop alert carries "exits not reviewed today", no exits run, and
     the next session blocks new entries for every book (`BEFORE_EXITS`). The fail-closed path in `fill` is only for
     `AccountWriteRefused` (the account lock) and `OrdersRefused`.
   - **Fix:** write row (b) as E2c's real rule. If the owner wants exits to still run after a Drive write fails, that
     is a change to E2c, judged there, not O2.
2. **One book's failure: there is no second book in the real run.**
   - `build_daily_run` defaults to `books=(BOOK1_RULES,)`, and O1's `build_day_runner` passes no other book. Book 2
     (`BOOK2_HYBRID`) has no orders or exit rules in the daily run until F5/F6.
   - Criterion 6 builds the run through `fno/daily/wiring.py` and fails if anything but an outside service is
     replaced, so the suite cannot get a Book 2 without breaking criterion 6.
   - **Fix, pick one and say it:**
     - (a) a named test-only second book, injected through `build_daily_run`'s `books`, orders and exit rules,
       written down as the one allowed exception to criterion 6;
     - (b) move the family to Known limits until F5/F6, keeping E3's existing per-book isolation tests (judge 84) as
       the evidence for now.
3. **Kill and rerun: "byte-identical for every step" is false while the quote parts run.**
   - A kill after any step from `quotes` to `exits` (steps 1-11 of the 13) kills the quote parts with the run. On the
     rerun, `quotes` is recorded, so no part restarts. `quotes_done` records `failed` with `NOT_IN_THIS_RUN`, and the
     parts' files stay uncommitted.
   - That is O1's judged rule (judge 178 addendum 2, note 4 declined; O1's Known limits), so the final run log
     differs from an uninterrupted day.
   - **Fix:** criterion 4 and the row name that outcome for those kills: `quotes_done` failed with its reason, the
     part files not committed, the hand fix in the claims. Keep byte-identity for everything else: the desk's
     records, the private records and the run log apart from `quotes_done`.
   - Also add a kill between a step's record and its commit (`PendingCommitter`'s case), the case E2b built the
     pending file for.

## Notes (not should-fix)

- **A. Drive outage (a).** "No step runs" is right, and it also means the 3 pm quote parts never start, so the
  NIFTY and NSE recordings are lost that day. NSE does not need Drive. Write it in the row so the owner sees it.
  Whether `quotes` should start before the download is O1's design question (raised with O1, not O2's to change).
- **B. A gap the suite will find (criterion 3).** E4c's refusal path in `fill` prints the send outcome itself
  (`print(outcome)` when it is not `SENT`). Under O1's `ReportedAlerts` the same unsent alert is then printed twice
  ("outcome | text", then "outcome"). By criterion 7 that goes to its owner (E4c or O1), not into a test that
  expects two lines.
- **C.** The routine-never-starts chain exists as described: O8's "never ran: no run log", and `NO_LOG` blocks every
  book on D+1. The text should note that `NO_LOG` reads "stopped before any step", which also covers a run that never
  began.
- **D.** "13 steps today" is right for O1 at f01bf9d7. E8's and M2's steps will add two, so read the count from
  `DAILY_RUN_STEPS` rather than typing it.

Coordination: no other row in `docs/WORK_REGISTER.md` covers an end-to-end failure suite, and LM1, E4c and the
first-line story are kept apart as stated. No duplicate.

## Addendum 1: revision 3 at 3050495d

**Verdict: PASS.** All three should-fixes and all four notes are applied, and each matches the code.

- **Should-fix 1.** Row (b) now gives E2c's rule: `PrivateFilesUnavailable` is a `CommitFailed`, so the run stops at
  `fills` and no exits run that day, the stop alert names "exits not reviewed today", and `BEFORE_EXITS` applies the
  next session. Only `AccountWriteRefused` and `OrdersRefused` fail one book closed. Any change to this belongs to
  E2c.
- **Should-fix 2.** One named test-only book, `book_test`, comes in through `build_daily_run`'s existing `books`
  parameter. It is written down as the single exception to criterion 6, and the row now names the real exceptions
  (`OrdersRefused`, `AccountWriteRefused`, an exit review that raises).
- **Should-fix 3.** For kills from `quotes` to `exits`, the expected outcome is now named: `quotes_done`
  `NOT_IN_THIS_RUN`, with the part files uncommitted. Every other kill must leave the records byte-identical. A kill
  between a step's record and its commit is added, and the step count is read from the tuple.
- **Notes A-D.** All in: the download failure loses that day's quote parts, NSE included; the double print is a Known
  limit, routed to E4c's owner; `NO_LOG`'s wording also covers a run that never began; the step count is read from the
  tuple.
- **One-line note:** criterion 5 still says "each Book 2 failure". Write `book_test` so it matches criterion 6 and the
  family row.
