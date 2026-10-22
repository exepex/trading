# Judge 480: MS-P1h, the frozen comparison card

**Scope:** story/ms-p1-card at ff6c813a (builder session_01WeFYCqffRe7et1nfSJyuv5), diff 756e6545..ff6c813a only (part
a is Judge B's). Story MS-market-school.md part h and its Claims. Lane 1 (evaluation records). Round 1 of 2.

**Verdict: FAIL.** 1 blocking, 3 should-fix, 4 minor. Judge H (session_01KNkZVoWvXMkoihKrrXk5Xa; the claim row of 480
carries "session_judgeH" by my mistake).

## Criteria
| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | A card registered after a decision: not counted | MET | `counting.py:73-76` strict ancestry; real-git tests; plants 1, 5 caught |
| 2 | A changed card SHA-256 refuses counting | MET | `counting.py:70`; plant 2 caught; D6 row after decision refused on real git (plant 12 caught) |
| 3 | Five roads on one day: one cluster | MET | `clusters.py`; plants 9, 10 caught |
| 4 | `read_card` accepts the card | MET | measurement yes, hypothesis no, trial 99 (free on main); charges SHA `5177fb36...` recomputed by me |
| - | One measurement card, no Holm family | MET | factory block `hypothesis: no`, `measurement: yes` |
| - | PS5 = trial 94, KL1 = trial 76 | MET | `research/ledger.csv` lines 95 (BANKNIFTY SF TP50) and 77 (NIFTY SC3 EXP) |
| - | First counted session unset | MET in the card, NOT protected in code | finding 1 |
| - | D6 change: old rows unaffected, malformed refused | MET | `journal/versions.csv` is header-only; 3 books render byte-identically; `cs1@1`, `@0`, `CS1@1x`, prefix-only refused; CLI registers `school:CS1@1` and refuses `school:cs1@1` (my run, then reverted) |
| - | Gates | MET | pytest -n auto 10295 passed, 16 xfailed; ruff check/format, check_imports, check_records, check_numbers clean; largest new file 76 lines |

## Findings
1. **Blocking: `school.first_counted` can be set or moved after the decisions.** `CountingRule` reads the date from
   settings at evaluation time and asks nothing of git (`counting.py:58-61`). My run: a 2 Nov decision is
   `before_first_counted_session` with 30 Nov, and `counted=True` once the date is moved back to 2 Nov after the fact.
   The card's §5 promises "in a commit made before that session's decisions"; nothing enforces it. Moving the date
   (back to add good days, forward to drop bad ones) is the cherry-pick the frozen card exists to stop. Expected: the
   commit that set the current `first_counted` value is a strict ancestor of the decision's commit (D6-style pickaxe
   on config.yaml), and a change after counting began is visible (a named reason), with real-git tests for both.
2. **Should-fix: any later card edit un-counts every earlier decision, contrary to the card's own versioning text.**
   `last_commit(CARD_PATH)` is the card's newest change at HEAD (`wiring.py:24`), and `CARD_PATH` is fixed. The card
   says a changed cost model, road, slot or denominator "is a new card version, never an edit", and
   `test_card.py` forces that card edit when `charges:` changes (a SEBI or STT change, as in Apr 2026). Then all
   v1 decisions stop counting. Expected: either the decision names the comparison card's SHA-256 (or version) and the
   rule checks that version's own freeze commit, or the card and story say plainly that any change voids all earlier
   counting, with the orchestrator's decision.
3. **Should-fix: the card is wrong or incomplete in places, and it can't be fixed after the freeze without
   finding 2's effect.**
   - "98 counted trials": EDGE1 is trials 71-98, 24 tradeable variants (`research/edge1/RESULTS.md` line 6).
   - "found no simple option rule beating costs" overstates RESULTS ("does not prove that no edge exists").
   - The story names "the denominator and bands of 3.5", but the card freezes no band (strikes of the money, which
     card's `band_steps` sets a road's gate) and no "impossible" bound (EDGE1's bounds are not cited).
   - PS5's and KL1's roads (BANKNIFTY-M, NIFTY-M) are not named.
4. **Should-fix: DRY.** `GitCardHistory` is a second git subprocess adapter beside `fno/research_engine/ledger.Git`,
   which already has `is_ancestor` (with the empty-commit guard), `commits_touching` (its last entry is the last
   change) and `is_shallow`. The test's `RegistryHistory` re-implements `Git.first_commit_containing`. Expected: one
   thin adapter over `Git`, and `Git` itself in the test.

**Minor (fix with the round):**
- (a) `test_the_card_leaves_..._names_no_driver_sha_yet` checks no driver SHA.
- (b) `test_the_registered_sha_is_the_one_in_the_card_constant` tests only a fixture.
- (c) CLI `_book` is untested (both plants survived; `parse_versions` still refuses).
- (d) `clusters.py` and the card say the common group is "frozen once before counting", but nothing freezes it.

## Plants
15 planted, 12 caught. Survivors: `CARD_COMPONENT` renamed (the same constant is on both sides, so part e must use
it), and the two CLI `_book` plants (minor c).

## Notes
- The D6 rows and ledger row 99 are still open, as the Claims say. A PASS here won't cover them. They wait for part e,
  and the orchestrator goes next.
- `build_counting_rule` has no caller yet; it waits for the join-up.
- In a shallow clone the card check fails safe (it doesn't count). D6's pickaxe has its own shallow risk, which comes
  from D6 and isn't this diff's.
