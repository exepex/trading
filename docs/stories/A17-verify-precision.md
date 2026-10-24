# A17 verify precision: `global-cues verify` compares at the copy path's precision (DRY1 row c4)

Owner: A16b/A17 builder (session 01MBnbVU4sundxNjs5u4xCsP). Lane 1 (a record check). Branch
`story/a17-verify-seconds`. Asked by the orchestrator on 23 Oct 2026 after the dry run DRY1 (row c4).

## Problem

- `python -m fno global-cues verify` exited 1 on all 1,981 `usdinr_fbil` rows. An example line: "first seen
  2026-10-15 06:16:31+05:30 before its copy was fetched 2026-10-15 06:16:31.010317+05:30".
- Every other cue verified. The data is fine; the check was wrong.

## Root cause (strong evidence: code, history and a real run)

1. The fill logs each copy's fetch time to the microsecond (`collector.py`). The copy's path keeps only whole seconds
   (`<HHMMSS>_<name>`).
2. On 15 Oct, A17d moved FBIL's table to Drive with `adopt`. `adopt` stamps a row's `first_seen_at` from the copy's
   path, so it is cut to the second. Those copies had already been logged by the fill at 06:16:31.010317, and adopt
   does not log an already-logged path again.
3. `verify.py` took the log's fetch time and compared strictly (`seen < fetched_at`). So every adopted row of an
   already-logged copy was 10.3 ms "early".
4. Response 158 recorded that 10.3 ms difference as a stated deviation at the time. The verifier was never adjusted.

Why other cues are not affected: the four US-index files adopted earlier (A17b) were never logged before adopt, so
their log row is the path time itself and the two times are equal. A fill row's `first_seen_at` is the fetch time
itself. No other compare in `fno/` sets a time taken from a path against a logged time (searched: the other
`first_seen_at` compares are against cutoffs).

## Fix

`verify.py` compares `first_seen_at` and the copy's fetch time cut to whole seconds, the copy path's precision
(`_to_copy_second`, with the reason in its docstring). Recorded rows are never rewritten, so this is the only fix
that keeps the 1,981 rows as they are. `adopt` is unchanged: a later adopt of a logged copy is rare, and any such
row is now checked at the path's precision.

## Claims

1. **A test reproduces the false failure through the real path:** a fill whose clock has microseconds, then `adopt`
   of the same logged copy (`tests/global_cues/test_verify_precision.py`). It fails on the old strict compare and
   passes with the fix.
2. **A row really seen before its copy's second still fails:** planted rows at 06:16:30 and 06:16:30.999999 against
   the copy of 06:16:31.010317. A first-seen time written in UTC is compared as the same moment: 00:46:30 UTC fails,
   00:46:31 UTC passes.
3. **Plants (the code deliberately broken, then put back):**
   - the old strict compare: 2 tests fail;
   - the check removed: 4 fail;
   - minutes instead of seconds: 3 fail;
   - a naive (time-zone-less) compare: 1 fails;
   - only the fetch time truncated: 0 fail. That one is an equivalent mutant: a whole second `s` satisfies
     `seen < s` exactly when `seen` cut to the second is before `s`, so no test can tell the two apart.
4. **Real data, read-only, 23-24 Oct:**
   - `global-cues verify --cue usdinr_fbil` exits 0 with the fix and exits 1 without it (the same lines as DRY1);
   - `global-cues verify` on every cue exits 0 with the fix ("every cue row equals the archived copy it names").
5. **Gates on the branch:** the full suite has 14,779 passed. `ruff check`, `ruff format --check` and
   `tools/check_imports.py` are clean.
