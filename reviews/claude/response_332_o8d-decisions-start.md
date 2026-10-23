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
