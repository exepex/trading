# Response 332: O8d, the desk run judged by when its decisions were collected (claims)

Builder 012eM7Ti (O8's owner), 23 Oct 2026. Branch `story/o8d-decisions-start`. Lane 1: it changes a health record's
verdict.

## The bug (strong evidence: the committed run logs)

The orchestrator's dry run (`docs/dryruns/DRY1_2026-10-23.md`, finding f3) and builder 013xqa traced it. O8's
`RunLogCheck` judged the `decisions` step's **finish** time against the bare decision deadline (15:12). E3 starts
that step **at** the deadline. Its own rule (`fno/desk/daily_steps.py:95`) is that the start must come within
`deadline + COLLECTION_GRACE` (30 s). It records what was visible at that start and fails closed after it.

So the old check missed by the step's own run time every day. From `journal/runs/`:

| Session | started_at (IST) | finished_at (IST) | Old verdict |
|---|---|---|---|
| 19 Oct | 15:12:00.0002 | 15:12:01.22 | late |
| 21 Oct | 15:12:00.0003 | 15:12:01.23 | late |
| 22 Oct | 15:12:00.0003 | 15:12:01.60 | late |
| 23 Oct | 15:12:00.0003 | 15:12:01.33 | late |

It had not shown in a message yet, because "Desk daily run" has no `live_from`. It would have read late on every
session from its first live day.

## The fix

`RunLogCheck` (`fno/health/desk_checks.py`) judges the step's `started_at` against `deadline + COLLECTION_GRACE`. It
imports E3's constant, so the two cannot drift. "No decisions step yet" waits for the same instant. An unreadable start
time is `unknown`.

## Tests (`tests/health/test_desk_and_data_checks.py`)

- **Boundary from E3's constant:** a start exactly at the grace is ok; one second later is late.
- **The four real run logs:** none reads late. Some of them still read `missed`, because other O1 steps were not run
  or failed on those days, which is correct and unrelated.
- **On the old code:** 5 of these tests fail (all four real days, and the boundary).

**Gates:**
- pytest: 14,776 passed, 1 skipped, 16 xfailed;
- ruff check and format clean;
- `check_imports` clean;
- `check_records` clean;
- `check_numbers` clean.

## Judge 552 (round 1 FAIL, tests only) addressed

**Should-fix, accepted.** `_run_log` wrote `started_at == finished_at`, so a check judging the finish against
deadline + grace passed every test. The helper now takes a separate finish time, and
`test_the_start_decides_never_the_finish` pins three cases:

| Started (s after the deadline) | Finished | Status |
|---|---|---|
| 29 | 31 | OK |
| 31 | 31 | LATE |
| 31 | 29 | LATE |

The judge's plant (judge `finished_at`) now fails 2 tests.

**Minor 1, taken in this round (orchestrator), one source of truth.** E3 reads its own clock a few ms after the run
log's start is taken. When E3 failed closed, every book carries `NO_DECISION_LATE` with E3's `COLLECTED_LATE` text.
O8 now reads that verdict first (`_collected_late`), and the start time only when it is absent. Only E3's
`COLLECTED_LATE` text counts. A book that committed nothing in time (`NO_DECISION_LATE` for its own reason) is not
read as a late collection.

Tests:
- `test_e3s_own_collected_late_verdict_wins_over_an_on_time_start`;
- `test_a_book_late_for_its_own_reason_is_not_read_as_a_late_collection`.

**Minor 2, taken.** `test_no_decisions_step_waits_for_the_same_grace`: at +29 s it is not due; at +30 s it is missed.

**Minor 3 (pre-existing), a follow-up in the register row:** O8 never reads the books' `NO_DECISION_LATE` as its own
problem.

**Plants (each fails a test):**
- judge `finished_at` instead of `started_at` (2 fail);
- E3's verdict ignored;
- the bare deadline for "no decisions step";
- any book-late reason taken as a late collection.

## O8e: judge 552.1's notes (follow-up after the merge, orchestrator's go)

**The orchestrator's question: does E3 mark the step late when every book is COLLECTED_LATE, or any one?** E3 writes
`COLLECTED_LATE` in one place only, `_all_late` (`fno/desk/daily_steps.py:96, 124`). It runs once, from the step's one
start time, gives every book the same reason, and returns before any per-book work. A book late for its own reason gets
`NOT_COMMITTED` (`:102`). So "every book" is E3's behaviour, and one book carrying it is enough. The code (any one) was
right; the docstring is corrected to say why.

**A mixed log cannot come from E3.** COLLECTED_LATE on some books only means an edited or broken run log. It reads
LATE and is named: "run log inconsistent: COLLECTED_LATE on some books only (...)" (orchestrator). Test:
`test_a_mixed_log_is_late_and_named_inconsistent`.

**Judge 552.1's surviving plant is now caught:** `test_the_late_text_under_another_decision_is_not_a_late_collection`
(the COLLECTED_LATE text under a decision other than `NO_DECISION_LATE` is not a late collection).

**Plants:**
- the decision filter dropped (fails 1 test);
- the mixed log not named (fails 1 test).
