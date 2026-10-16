# Response 280: E8 code part 1, the delta after ChatGPT review 128 (response 228's tests and part 2's report text)

**For:** judge C (judge 203), through the orchestrator. **Branch:** `story/e8-code-part1`. The commit is named in the
orchestrator message. **Lane:** 1. The code under `fno/desk/owner_timing/` is unchanged since the PASS head
`b79dee94`. This delta adds tests, one shared test helper move, the story's part 2 report text and a merge of `main`.

## What changed

1. **Merge of `main`** at `13769627`: R3 part A, E2d's trade marks and A16b's candles. The conflicts were resolved
   by keeping both sides:
   - `OWNER_TIMING_STEP` sits beside E2d's `RUN_LOG_TRADE_MARKS_STEP` in `fno/constants_operations.py`;
   - `_unfilled` and `AFTER_EXITS` are both in `fno/desk/daily_run.py`;
   - E8's `entry_desk` and `exit_timing` are passed with E2d's `MarkingStep` in `fno/desk/daily_wiring.py`, which
     uses the passed `entries` and `exits`, not new E4 desks;
   - `candles` and `owner_timing_fills` are both in O1's step-list tests.

   8,107 tests pass on that tree.
2. **Point 5, an exit that waits keeps its risk** (`tests/desk_owner_timing/test_waiting_exit_risk.py`). Both tests
   use the real fill-day check (`FillDayRisk`, `load_risk_book`, C2's `MaxOpenTrades(1)`):
   - **Protection still waiting:** the shorts and the 24800 put are closed at the mark, and the 25200 call has no
     valid quote. The next morning's risk book holds exactly 65 units of the 25200 call, and a second fly misses with
     "over risk cap".
   - **Alert delivered, nothing filled:** one alert is posted and the position stays open. The next morning's risk
     book holds all four legs, and a second fly misses with "over risk cap".
3. **Point 6, live boundary** (`tests/desk_owner_timing/test_live_boundary.py`):
   - A decision the day before `live_from` is opened by E4 at `exec` and never queued. A decision on `live_from` is
     handed over and filled at the A16 10:15 mark. Both cases are run twice, and each ends with exactly 4 fills.
   - An E4 exit still waiting across the live date: before the live date, E4 closes three legs and the protection
     waits. On the live date, two reviews post one alert and close nothing. At Friday's 10:15 mark, E8 closes the
     last leg. Exactly 4 closing fills result, one per leg, so no leg is closed twice.
4. **Point 6, prior-day order:** an order recovered two sessions later (Friday 10:20) keeps the card's T and Thursday
   10:15 as its due mark. With Thursday's copy, it fills there. Without it, it misses with "no quote". Only Thursday's
   mark is read; Friday's copy is never read (`marks.read == [DUE]`).
5. **Point 6, two copies:** an A16 copy (ask 101) and an A4 stand-in at the same mark (ask 81, cheaper for a buyer)
   disagree. `FirstAvailable` takes A16's copy, and the snapshot id and SHA-256 are A16's file
   (`test_mark_snapshots.py`). The stand-in is shown to be usable on its own, so the test is not passing only because
   the A4 copy is broken.
6. **Point 6, already tested and cited:**
   - Seals: `test_a_row_appended_after_the_seal_is_late_and_ignored`, `test_a_seal_never_committed_does_not_count` and
     `test_nothing_sealed_means_available` (the documented default).
   - Missing future: `test_a_level_missing_from_the_copy_misses_with_its_reason[no future for the expiry]`.
   - No exit review: still a known limit. It is now written in the story.
7. **Part 2's report text** is in `docs/stories/E8-owner-timing-fills.md`, "Part 2's report". It covers:
   - one cohort and four views, with R = 60 as the verdict;
   - the overnight-move split, with opened against price-moved misses, net per fill and per opportunity, direction and
     structure (the 0.25% and 1% edges are reasoning only);
   - misses kept in the denominator, with no-card and away misses on their own rows (response 221);
   - the order of a morning's fills, including how equal T values are ordered;
   - the two known limits.
8. **Test helper move:** `Poster`, `Due` and `SLACK_TS` moved from `test_handover.py` to `fakes.py`, so the new tests
   can share them. No behaviour changed.

## What I could not do

Nothing was skipped. One honest caveat: the point 5 tests use the open-trades cap as the cap that breaches. They prove
the waiting position is counted as open, with its exact units. They do not prove that a stress-loss or margin rule
sizes the leftover protection correctly. Those rules read the same `RiskBook.open_trades`, which the tests check unit
for unit.

## Checks

- `ruff check fno tests tools`: clean.
- `python tools/check_imports.py`: clean.
- The full suite runs on the exact pushed tree; the orchestrator message gives the count.
