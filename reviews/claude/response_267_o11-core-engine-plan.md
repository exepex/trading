# Response 267: O11, the core engine plan and the end-to-end acceptance replay (for Judge E and a lane-1 judge)

Builder session_01FWkBH4zNAEFSEpjUzVEgnd; orchestrator session_01VG1RqxLFUVdvvPuMRYZtDH.

## What to review

| Item | Where | Lane |
|---|---|---|
| Core engine plan, revision 2 | `docs/CORE_ENGINE_PLAN.md` on `story/o11-core-engine-plan` | 2 (docs), Judge E |
| O11 story text | `docs/stories/O11-e2e-acceptance.md` on `story/o11-e2e-acceptance` | 1 |
| O11 harness (tests only) | `tests/e2e_acceptance/` on `story/o11-e2e-acceptance` | 1 |

## Claims, each with its check

1. Every owner quote in the plan's section (a) is on the cited line (checked by grep; one wrong citation replaced).
2. Revision 2 takes the orchestrator's owners (16 Oct) for every gap the first version called ownerless, and adds
   the go-live gate (DESK_DECISIONS row 247) as the definition of done, the last step of the critical path, and a
   "trial evidence" column for every expectation.
3. Three gaps are still unowned, said plainly: T1c (the card prints "M1 pending" although M1 is merged), O1's 14:05
   start (a follow-up of O1's builder), and the owner's `daily.live_from` dates (all null).
4. O11 replays 16 Oct 2026 through O1's run (in-process commands behind O1's `DayStep`, O1's real `Alerted` and
   `ReviewsStep`): 11 tests pass and 16 strict xfails name what is not built. Each xfail fails for its intended
   reason (checked with `--runxfail`).
5. Gates on the merged tree: the full suite, `ruff check`, `ruff format --check`, `tools/check_imports.py` and
   `tools/check_records.py` (numbers in the commit message of the O11 head).
6. Mutations caught: C4's listing lookback set to 0, marks forced to awaiting settlement, `PACKED_BOOKS` emptied.

## What is not real in the replay

See the story's inputs table: the restated contract IDs, a synthetic NSE listing file, one approved test strategy,
fixed live features, and the 15:15 snapshot re-timed from the 14:55 rows.
