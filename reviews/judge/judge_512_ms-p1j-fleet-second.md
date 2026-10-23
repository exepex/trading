# Judge 512: MS-P1j, the fleet join-up (second judge)

**Scope:** story/ms-p1j-fleet at 8d4d6fb2 (builder session_01CmKJ6taCLzfEGg7wt6RC4N), the whole branch against `main`
(merge base a172320a). Story MS-market-school.md MS-P1j and "MS-P1j Claims" rounds 1-4. Lane 1, a money piece:
second judge under "Two judges for money pieces". I wrote this without reading Judge B's 507. Round 1 of 2.
Judge K (session_019ZApRwkUiNMKDsf1k4W44z).

**Verdict: FAIL.** 2 should-fix, 1 minor. The design holds and the evidence reproduces. The composition root's
replay isolation, and six guards on record and fill paths, can be broken with every school test green.

## Criteria
| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Off prints "school off", writes nothing | MET | CLI switch plant caught; the CLI builds nothing when off |
| 2 | One sealed outcome per scheduled (road, driver) | MET | the card's-roads plant caught; my replay gives 42 = the cards' roads |
| 3 | A rerun seals nothing twice | MET | rerun-branch, refill, re-record, fast-path and mark plants caught. My rerun into the same replay folder: "0 fills", all 69 files unchanged |
| 4 | i's harness on the real wiring | MET | `test_acceptance_real.py` 9 passed, none skipped (my run) |
| 5 | End-to-end dry run | MET | my `school run --replay` for 22 Oct: 42 decisions, 16 fills, 69 files. A second replay is byte-identical (69 of 69 hashes). `git status` is clean afterwards |
| - | Crash and rerun finish (recorded fills read back, outcomes sealed once, `recorded_for`) | MET | plants caught: openings/closings re-priced, settlements of every session, `recorded_for` filter |
| - | Entries before exits on a shared size | PARTLY | exits ranked with entries: caught. Ticket entries vs account exits: not (finding 2) |
| - | Tickets vs real positions (ruling d) | MET | the second-ask plant and the real-positions-only filter caught |
| - | Driver time limit times only the driver's code | MET | Claims' plant; `isolated` narrowed to `KeyError` caught |
| - | Live guard on unmeasured quotes | MET | guard plant caught |
| - | `PreviousSlotToday` writes no record | MET | hash-identical test; the source-session plant caught |
| - | Touches to a, f, g, i | MET | each is one parameter or field, read in full; g's sections are byte-identical with reports off (g's tests) |
| - | Gates | MET | see Notes |

## Findings
1. **Should-fix: the replay's isolation is not tested at the composition root.**
   - `build_fleet` (`fno/school/wiring.py`) is never called by a test; two tests monkeypatch it away.
   - My plant: `dashcam = build_dashcam()` in replay (line 68). Every school test still passes. With it, `school run
     --replay` (the dry run's own command) would seal into the real Drive dashcam and push receipts to `main`.
   - The same is true of the committer and the account sync.
   - Expected: a test that builds `build_fleet(cfg, RunMode.REPLAY, ...)` with the Drive, dashcam, committer and
     account-sync builders patched to raise, and asserts every store sits under the replay folder.
2. **Should-fix: six more guards survive deletion** (all with `tests/school` green):
   - `decide.py:115` `_check_identity` removed. A driver returning another road's or session's decision is sealed
     under that road (`records.decision_record` uses `decision.road`).
   - `counts_file.py:59`: the opportunity file's write-once check removed. That public record can then change.
   - `fill.py:65`: drift rows for every priced entry, not only the served ones. A `size_shared` entry that never
     opened gets drift rows.
   - `shared_size.py:56` `(is_exit, is_ticket)` swapped. That serves account exits before ticket entries, against
     the frozen "entries first (accounts, then tickets), exits from what is left".
   - `quote_share.py:37`: the share counted from the named reason only. A quote refusal behind a stop then drops
     out of the per-road quote share, the orchestrator's 22 Oct requirement. Round 3's test pins `reason_counts`,
     not `quote_shares`.
   - `settle.py:39` `<` made `<=`. Expiry-day positions then settle before their own slot whenever the settlement
     file exists (a replay of a past day).
   - Expected: one test per guard that fails when it is removed.

**Minor:** the remaining survivors are equivalent or replay-only, so no test is required. Say so in the Claims:
- passing all positions to `decide` (cards filter by road);
- `PreviousSlotToday`'s rule-only filter (g's section filters again);
- a `None` entry mid as 0.0 (a filled leg's quote is two-sided);
- the replay store's conflict check.

## Plants
40 planted, 29 caught. Survivors: the seven in findings 1 and 2, and four in the minor.

## Notes
- **Gates (my run, python3 after routine setup):** pytest -n auto 12,099 passed, 16 xfailed. ruff check and format,
  check_imports and check_records are clean. The largest fleet file is `decide.py` at 145 lines.
- Open by design, as the Claims say: `allocate` reads sizes through d's `QuoteRules` only after d's part 4 reaches
  `main`. Until then a missing size reads as 0 (no fill), which fails safe.
- A late rerun prices entries again at the 15:00 snapshot. That is accepted by ruling b, and the run marks it in the
  evening section.
