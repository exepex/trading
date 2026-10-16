# Judge 247: O9 step 2a, one taker per A16 mark (lane 1)

Verdict: **FAIL** at `72753fa3` (`story/o9-step2a-recorder`, stacked on step 1 `aa79450b`, judge 242).
One must-fix: a single failed claim push locks every later push of the run.

## Claims vs reality
| Claim (O9 section 6, items 1, 2, 4) | Reality | Status |
|---|---|---|
| A claim file is committed before each mark; git decides; the loser skips the mark | `GitMarkClaims` plus `GitManifestRecorder(-X theirs)`. The builder's two-clone race test holds: exactly one run wins and the loser keeps the winner's file. | met |
| Claim made 45 s before the mark | Met. My mutation setting the lead to 0 is caught. | met |
| Unreachable origin gives UNCLAIMED and the mark is taken anyway | Met for that one mark. **What happens to the run afterwards is broken (must-fix 1).** | **broken** |
| Failed quotes retried once at the same pace; Groww's code kept, never the message | Met. I checked the published SDK (growwapi 1.5.0, `exceptions.py:33-41`, `client.py:1501`): `GrowwAPIException` carries `.code` taken from the `status: FAILURE` body. | met |
| Alert says the realised variance is unaffected when the streak is only `incomplete` | Met. In `status.verdict`, `incomplete` only ever means the index check passed. | met |
| 8 tests; mutations caught; 6986 passed | 8 tests pass. The trial merge with main (f9fa6695) passed 7000 tests. ruff, format and imports are clean. | met |

## Must-fix
1. **Two committers in one checkout refuse each other's unpushed commits, so one GitHub blip stops all publishing for the rest of the run.**
   - The cause: `GitManifestRecorder.pull` refuses when `origin/main...HEAD` holds any path the committer does not own (`manifest_commit.py`, `OFF_MAIN`). The claims committer owns only `receipts/intraday/claims/`. The ledger committer owns only `ledger/`, `rv/` and `heartbeat.json`.
   - The sequence: a claim commit whose push fails (fetch error, or three rejected pushes) stays local. From then on, the ledger committer refuses because of the claim file. The next claim refuses because of the ledger commit. Each committer's leftover then blocks the other indefinitely.
   - Before 2a there was one committer, so it always owned its own leftovers, and the next mark recovered on its own.
   - Reproduced on two clones of a bare origin, with only the existing classes. Origin was unreachable for the 09:15 claim and back for everything after it:
     ```
     1 unclaimed  claim NOT committed: pull failed: ... missing.git does not appear to be a git repository
     2 intraday files NOT committed: pull failed: ... changes not on main outside this writer's paths: receipts/intraday/claims/.../0915.json
     3 unclaimed  claim NOT committed: pull failed: ... outside this writer's paths: research/data/intraday/ledger/x.csv
     4 ledger pull refused: ... receipts/intraday/claims/.../0915.json, .../0930.json
     origin main: start   (nothing published after the blip)
     ```
   - Consequences:
     - Every later mark is UNCLAIMED, so two overlapping runs take every mark again. That brings back the 429 losses of 74-87 quotes this step exists to stop.
     - Ledger rows, the realised variance and the heartbeat stay in an ephemeral container until the run ends, then are lost.
     - The O8 health check sees no push.
   - The trigger is the same transient failure that UNCLAIMED was built for, so this is not far-fetched.
   - The fix belongs in the design, not a retry patch. Make one owner of all of the run's paths, so that every leftover is publishable by whichever commit runs next. Two ways to do that:
     - the recorder's ledger committer also owns the claims tree; or
     - a single owned-paths committer serves both writers.
   - Required test: the sequence above, ending with origin `main` holding both claims and the ledger row once origin is back.

## Follow-ups (not blocking)
2. My mutation removing `self._lost.add(mark)` survives (199 passed). With it removed, a run would ask again for a mark it lost on each later call until the winner's row arrives. Add a test that a lost mark is never asked for twice.
3. My mutation making the dry-run path return `GitMarkClaims` survives. No test pins that a dry run never commits claims to `main`. Since this is an outward write, add one.
4. A run that dies after claiming a mark leaves that mark untaken. The design accepts this (45 s lead), but the ledger will then show it as `missed`. Name that cause in the alert or the run note so a gap is not misread.
5. A retried quote lands up to about 45 s after the first pass (224 quotes at 5 per second). Its own times are kept, so later readers can see it is later. The note `quotes_retried:n` should stay next to those times in the ledger row.

## Project rules
- All files are under 350 lines.
- Constants are at the top of each module.
- Concrete classes are wired only in `fno/intraday/wiring.py`.
- No secrets. The exception message is never kept.
- No order code.
- The register row should name step 2a when it is resubmitted.

## Gates
Trial merge with `origin/main` (f9fa6695):
- `pytest -n auto`: 7000 passed.
- `ruff check` and `ruff format --check`: clean.
- `check_imports`: clean.

## Mutations by the judge (against `tests/intraday`)
- 6 of 8 caught:
  - the published check removed;
  - `_published` made always true;
  - the claim lead set to 0;
  - the streak rule changed from all to any;
  - the code-length guard removed;
  - the retry note removed.
- 2 survived: `_lost` and the dry-run claims (follow-ups 2 and 3).
